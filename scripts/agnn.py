# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "numpy",
#     "load-atoms",
#     "matplotlib",
#     "ase",
#     "mendeleev",
# ]
# author = "Stefan Bringuier <stefan.bringuier@gmail.com>"
# description = "Basic numpy Atomic Graph Neural Network with Message Passing"
# license = "MIT"
# keywords = ["atomic","graph", "neural network", "message passing"]
# classifiers = [
#     "Programming Language :: Python :: 3.10",
#     "License :: MIT License",
#     "Operating System :: OS Independent",
#     "Intended Audience :: Science/Research",
#     "Topic :: Scientific/Engineering :: Chemistry",
#     "Topic :: Scientific/Engineering :: Physics",
#     "Topic :: Scientific/Engineering :: Artificial Intelligence"
# ]
# ///

from ase.neighborlist import neighbor_list
from ase.data import covalent_radii
from load_atoms import load_dataset
import numpy as np
import matplotlib.pyplot as plt
from mendeleev import element

# Use cache to speed feature assignment
print("Loading element data...")
ELEMENT_CACHE = {}
elements = [element(z) for z in range(1, 119)]
ELEMENT_CACHE.update(
    {
        z: {
            "nvalence": elem.nvalence(),
            "zeff": elem.zeff(),
        }
        for z, elem in enumerate(elements, start=1)
    }
)
print("... done")


def create_adjacency_matrix(
    i: np.ndarray, j: np.ndarray, n_atoms: int
) -> np.ndarray:
    """Create normalized adjacency matrix

    The adjacency matrix just informs us what nodes are connected to each
    other. In the message passing framework that aggregates information from
    neighbors by taking sums of the messages we can just take the dot product
    of the node feature matrix by the adjacency matrix to get the message
    passing step.

    See to learn more:
    https://ericmjl.github.io/essays-on-data-science/machine-learning/message-passing
    """
    A = np.zeros((n_atoms, n_atoms))
    A[i, j] = 1.0

    # Normalize adjacency matrix
    degrees = np.sum(A, axis=1)
    degrees = np.where(degrees == 0, 1e-8, degrees)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(degrees))
    A = D_inv_sqrt @ A @ D_inv_sqrt

    return A


def normalize_features(X: np.ndarray) -> np.ndarray:
    """Normalize node features to zero mean and unit variance.

    To understand why we do this, see:
    https://en.wikipedia.org/wiki/Feature_scaling
    """
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-8
    return (X - mean) / std


def create_node_features(
    atoms, cutoff: float, num_centers: int = 8
) -> tuple:
    """Create node features: atomic number, mass, covalent radius, basis
    expansion.

    When we first feed inputs into the GNN, we need to create node(edge)
    features. This is just a vector, matrix, tensor of features that is tied
    to each node(edge) on the graph. This is what we are trying to learn,
    that is which of these features are important on a node(edge) based on
    the graph structure and information passed from neighboring nodes(edges).

    Most of MLIPs are actually focused on the best set of node(edge) feature
    representations. A lot is centered around basis expansions and the update
    of the functions for the features. In this function we are just using
    basic atom properties and expanding the pair-wise distances into sampling
    of basis functions (radial and bessel functions).
    """
    i, j, d = neighbor_list("ijd", atoms, cutoff)
    n_atoms = len(atoms)

    # Atomic properties
    atomic_nums = atoms.get_atomic_numbers()
    cov_radii = np.array([covalent_radii[z] for z in atomic_nums])
    z_effective = np.array([ELEMENT_CACHE[z]["zeff"] for z in atomic_nums])
    nvalence = np.array([ELEMENT_CACHE[z]["nvalence"] for z in atomic_nums])

    # Compute radial basis expansion for each pair i-j
    centers = np.linspace(0.0, cutoff, num_centers)
    width = 2 / 3 * (cutoff / num_centers)
    num_bessel = 3
    rbf_features = np.exp(-((d[:, None] - centers) ** 2) / (2 * width**2))
    bessel_funcs = np.sin(
        d[:, None] * np.linspace(np.pi / num_bessel, np.pi, num_bessel)
    ) / (d[:, None] + 1e-8)
    basis_features = np.hstack((rbf_features, bessel_funcs))

    # We need to combine the contributions of all
    # neighbors j for i to aggregate which basis
    # functions contribute the most
    basis_aggregated = np.zeros((n_atoms, num_centers + num_bessel))
    np.add.at(basis_aggregated, i, basis_features)
    neighbor_counts = np.bincount(i, minlength=n_atoms)
    basis_aggregated /= neighbor_counts[:, None] + 1e-8

    # Combine features
    node_features = np.column_stack(
        (
            cov_radii,
            z_effective,
            nvalence,
            basis_aggregated,
        )
    )

    # Normalize features
    node_features = normalize_features(node_features)

    # Create adjacency matrix
    A = create_adjacency_matrix(i, j, n_atoms)

    return node_features, A


def load_and_preprocess(
    dataset_name: str, cutoff: float, slice=None
) -> list[dict]:
    """Load atomic structures and normalize energies.

    Uses the `load_atoms` package to load the dataset:
     https://jla-gardner.github.io/load-atoms

    Returns a list of dictionaries with the following keys:
    - X: Node features
    - A: Adjacency matrix
    - energy: Normalized energy
    - energy_mean: Mean energy
    - energy_std: Standard deviation of energy
    - n_atoms: Number of atoms
    """
    dataset_raw = load_dataset(dataset_name)
    if slice:
        dataset_raw = dataset_raw[slice]

    energies = [
        frame.info.get("energy", 0.0) / len(frame) for frame in dataset_raw
    ]
    energies = np.array(energies)
    energy_mean = energies.mean()
    energy_std = energies.std() + 1e-8

    data_list = []
    # For each structure, create the atom (i.e., node) features
    # and adjacency matrix and normalize targets.
    for frame, energy in zip(dataset_raw, energies):
        X, A = create_node_features(frame, cutoff)
        norm_energy = (energy - energy_mean) / energy_std
        data_list.append(
            {
                "X": X,
                "A": A,
                "energy": norm_energy,
                "energy_mean": energy_mean,
                "energy_std": energy_std,
                "n_atoms": len(frame),
            }
        )
    return data_list


def leaky_relu(x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """Leaky ReLU activation function.

    See:
    https://en.wikipedia.org/wiki/Rectifier_(neural_networks)

    """
    return np.where(x > 0, x, alpha * x)


def gnn_forward(X: np.ndarray, A: np.ndarray, params: dict) -> float:
    """Forward pass of the GNN with message passing.
    For each layer:
        1. Message passing: Multiply layer input by adjacency matrix.
        2. Update: Multiply with weight matrix and add bias.
        3. Activation: Apply the leaky ReLU.
    """
    H = X
    n_layers = sum(1 for k in params if k.startswith("W_layer"))

    for i in range(n_layers):
        M = A @ H
        Z = M @ params[f"W_layer{i}"] + params[f"b_layer{i}"]
        H = leaky_relu(Z)  # Leaky ReLU prevents dead neurons

    atom_energies = H @ params["W_readout"] + params["b_readout"]
    return atom_energies.sum()


def mse_loss(pred: float, target: float) -> float:
    """Mean Squared Error Loss"""
    diff = pred - target
    return 0.5 * diff**2


def gnn_backward(
    X: np.ndarray, A: np.ndarray, params: dict, pred: float, target: float
):
    """Backward pass of the GNN to compute gradients.

    See layer operations in the forward pass.

    Backward pass:
    1. Compute forward pass, store intermediate values for each layer.
    2. Compute gradients using chain rule, starting with output layer.
    3. Store each layer gradient in a dictionary.
    """
    H_vals = [X]
    Z_vals = []
    M_vals = []
    n_layers = sum(1 for k in params if k.startswith("W_layer"))

    for i in range(n_layers):
        M = A @ H_vals[-1]
        Z = M @ params[f"W_layer{i}"] + params[f"b_layer{i}"]
        H = leaky_relu(Z)
        M_vals.append(M)
        Z_vals.append(Z)
        H_vals.append(H)

    dL_dpred = pred - target
    loss = mse_loss(pred, target)

    grads = {}
    A_last = H_vals[-1]
    dL_dE = np.ones_like(A_last[:, 0]) * dL_dpred

    grads["W_readout"] = A_last.T @ dL_dE
    grads["b_readout"] = dL_dE.sum()

    dL_dH = dL_dE[:, np.newaxis] * params["W_readout"]

    for i in range(n_layers - 1, -1, -1):
        dZ = dL_dH * np.where(Z_vals[i] > 0, 1.0, 0.01)
        grads[f"W_layer{i}"] = M_vals[i].T @ dZ
        grads[f"b_layer{i}"] = dZ.sum(axis=0)
        dM = dZ @ params[f"W_layer{i}"].T
        dL_dH = A.T @ dM

    grads["loss"] = loss
    return grads


def init_params(feature_dim: int, hidden_dims: list[int]) -> dict:
    """Initialize GNN parameters with small scale for numerical stability."""
    np.random.seed(42)
    params = {}
    prev_dim = feature_dim
    for i, dim in enumerate(hidden_dims):
        scale = 0.01 / np.sqrt(prev_dim)
        params[f"W_layer{i}"] = np.random.uniform(
            -scale, scale, (prev_dim, dim)
        )
        params[f"b_layer{i}"] = np.zeros(dim)
        prev_dim = dim
    params["W_readout"] = np.random.uniform(
        -1e-4, 1e-4, prev_dim
    )
    params["b_readout"] = 0.0
    return params


def init_adam_state(params: dict) -> dict:
    """Initialize ADAM optimizer state (first and second moments)."""
    state = {}
    for k, v in params.items():
        state[f"m_{k}"] = np.zeros_like(v)  # First moment
        state[f"v_{k}"] = np.zeros_like(v)  # Second moment
    state["t"] = 0  # Time step
    return state


def adam_update(
    params: dict,
    grads: dict,
    state: dict,
    lr: float,
    beta1: float = 0.9e0,
    beta2: float = 0.999e0,
    eps: float = 1e-8,
):
    """Implementation of the ADAM optimizer.

    See algorithm 1 in:
    D.P. Kingma, J. Ba, Adam: A Method for Stochastic Optimization, (2017).
    https://doi.org/10.48550/arXiv.1412.6980.

    """
    state["t"] += 1
    t = state["t"]

    for k in params:
        if k in grads:
            # Get gradients and moments
            m = state[f"m_{k}"]
            v = state[f"v_{k}"]
            g = grads[k]

            # Update biased first moment
            m = beta1 * m + (1 - beta1) * g
            # Update biased second moment
            v = beta2 * v + (1 - beta2) * np.square(g)

            # Store updated moments
            state[f"m_{k}"] = m
            state[f"v_{k}"] = v

            # Bias correction
            m_hat = m / (1 - beta1**t)
            v_hat = v / (1 - beta2**t)

            # Update parameters
            params[k] -= lr * m_hat / (np.sqrt(v_hat) + eps)


def train_gnn(
    data_list: list[dict],
    params: dict,
    epochs: int = 10,
    initial_lr: float = 1e-5,
    l2_lambda: float = 1e-4,
    clip_value: float = 1.0,
    decay_rate: float = 0.98,
):
    """Train a GNN using ADAM optimizer with:
    1. Learning rate decay - prevents overfitting, allows for fine-tuning
    2. L2 regularization - prevents overfitting, penalizes large weights
    3. Gradient clipping - prevents exploding gradients, stabilizes training

    """
    adam_state = init_adam_state(params)
    plt.figure()
    losses = []

    for epoch in range(epochs):
        np.random.shuffle(data_list)
        epoch_loss = 0.0

        # 1. Learning rate decay
        lr = initial_lr * (decay_rate**epoch)

        for item in data_list:
            X, A, y = item["X"], item["A"], item["energy"]
            y_pred = gnn_forward(X, A, params)
            grads = gnn_backward(X, A, params, y_pred, y)

            # 2. L2 regularization
            for k in params:
                if "W" in k:
                    grads[k] += l2_lambda * params[k]

            # 3. Gradient clipping
            for k in grads:
                grads[k] = np.clip(np.array(grads[k]), -clip_value, clip_value)

            adam_update(params, grads, adam_state, lr)
            epoch_loss += grads["loss"]

        avg_loss = epoch_loss / len(data_list)
        losses.append(avg_loss)

        plt.clf()
        plt.plot(losses)
        plt.yscale("log")
        plt.savefig("plots/loss.png")

        print(f"Epoch {epoch+1}/{epochs}, Loss={avg_loss:.6f}, LR={lr:.2e}")


def evaluate_model(data_list: list[dict], params: dict) -> tuple:
    """Evaluate the model and return true and predicted energies."""
    y_true, y_pred = [], []
    for item in data_list:
        pred = gnn_forward(item["X"], item["A"], params)
        pred_total = (
            pred * item["energy_std"] + item["energy_mean"]
        ) * item["n_atoms"]
        true_total = (
            item["energy"] * item["energy_std"] + item["energy_mean"]
        ) * item["n_atoms"]
        y_pred.append(pred_total)
        y_true.append(true_total)
    return np.array(y_true), np.array(y_pred)


def plot_parity(train_true, train_pred, test_true, test_pred):
    """Plot parity plot for true vs predicted values."""
    plt.figure()
    plt.scatter(
        train_true,
        train_pred,
        alpha=0.5,
        label="Train",
        color="blue",
    )
    plt.scatter(
        test_true,
        test_pred,
        alpha=0.5,
        label="Test",
        color="orange",
    )

    combined_true = np.concatenate([train_true, test_true])
    plt.plot(
        [min(combined_true), max(combined_true)],
        [min(combined_true), max(combined_true)],
        "r--",
    )

    plt.xlabel("True Energy (eV)")
    plt.ylabel("Predicted Energy (eV)")
    plt.title("Parity Plot")
    plt.legend()
    plt.savefig("plots/parity_plot.png")
    plt.close()


def main():
    data_list = load_and_preprocess("QM7", cutoff=2.25)
    np.random.shuffle(data_list)

    split_idx = int(0.6 * len(data_list))
    train_data = data_list[:split_idx]
    test_data = data_list[split_idx:]

    feature_dim = train_data[0]["X"].shape[1]
    print(f"Feature dimension: {feature_dim}")

    # GNN architecture and initialization
    hidden_dims = [32, 32, 32]
    params = init_params(feature_dim, hidden_dims)

    # Training loop
    train_gnn(train_data, params, epochs=250, initial_lr=9e-4, decay_rate=0.99)

    # Evaluation
    train_true, train_pred = evaluate_model(train_data, params)
    test_true, test_pred = evaluate_model(test_data, params)

    # Parity plot for train and test data
    plot_parity(train_true, train_pred, test_true, test_pred)

    # RMSE for train and test data
    train_rmse = np.sqrt(np.mean((train_true - train_pred) ** 2)) * 1000  # meV
    test_rmse = np.sqrt(np.mean((test_true - test_pred) ** 2)) * 1000  # meV
    print(f"\nTrain RMSE: {train_rmse:.3f} meV")
    print(f"Test RMSE: {test_rmse:.3f} meV")

    # Print first test point prediction vs truth
    n_atoms = test_data[0]["n_atoms"]
    print("First test point:")
    print(f"Predicted total energy: {test_pred[0]:.3f} eV")
    print(f"True total energy: {test_true[0]:.3f} eV")
    print(
        f"Absolute total error: "
        f"{abs(test_pred[0] - test_true[0])*1000:.3f} meV"
    )
    print(f"Predicted per-atom energy: {test_pred[0] / n_atoms:.3f} eV/atom")
    print(f"True per-atom energy: {test_true[0] / n_atoms:.3f} eV/atom")


if __name__ == "__main__":
    """Run the script.

    4 Jan. 2025:
    - Training yields RMSE errors in the ~1200 meV range
      (mean prediction RMSE ~9000 meV)
    - Test RMSE ~1500 meV
    """
    main()
