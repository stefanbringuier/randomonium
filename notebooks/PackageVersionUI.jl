### A Pluto.jl notebook ###
# v0.19.22

#> [frontmatter]
#> author = "Stefan Bringuier"
#> title = "Package Version widget"
#> date = "2023-04-25"
#> tags = ["PlutoUI"]
#> description = "Idea for a potential widget in PlutoUI to show the package version of a notebook. This is useful for static HTML exports."
#> license = "Unlicense"

using Markdown
using InteractiveUtils

# ╔═╡ 337c098a-e1fd-4047-9cc5-c6d385d107f2
# Example pkg
using PlutoUI

# ╔═╡ b1691378-534d-4ce3-afc7-1611cb95e6e5
begin
	using Pkg: dependencies
	function installed()
	    deps = dependencies()
	    installs = Dict{String, VersionNumber}()
	    for (uuid, dep) in deps
	        dep.is_direct_dep && dep.name != "Pkg" || continue
	        dep.version === nothing && continue
	        installs[dep.name] = dep.version
	    end
	    return installs
	end
end;

# ╔═╡ 5e5e0a55-bc2a-4fc4-aebf-efd8987f7b71
begin
	pkgs_info = [(pkg, installed()[pkg]) for pkg in keys(installed())]
    pkgs_table = [("$pkg", "$(ver)") for (pkg, ver) in pkgs_info]
    pkgs_table = sort(pkgs_table, by = x -> x[1])
    table_html = join(
		["<tr><td>$pkg</td><td>$ver</td></tr>" for (pkg, ver) in pkgs_table], 
		"\n")
end;

# ╔═╡ e5cf2e05-a2d4-4fec-93d6-a2c27e95380c
pkg_css= HTML("""
<style>
        #pkg-table {
            position: fixed;
            top: 10%;
            left: 5%;
            width: min(80vw, 300px);
            overflow: auto;
            border-collapse: collapse;
			border-radius: 10px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.0);
            z-index: 100;
            transition: transform 300ms cubic-bezier(0.18, 0.89, 0.45, 1.12);
        }
        
        #pkg-table h3 {
            margin: 0;
            padding: 10px;
            background-color: #808080;
            color: white;
            font-size: 18px;
        }
        
        #pkg-table table {
            width: 100%;
            margin-bottom: 0;
            border-collapse: collapse;
        }
        
        #pkg-table td, #pkg-table th {
            border: none;
            padding: 5px 10px;
            text-align: center;
            font-size: 14px;
        }
        
        #pkg-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        
        #pkg-table tr:hover {
            background-color: #ddd;
        }
        
        #pkg-table .close-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            cursor: pointer;
            font-size: 20px;
            color: white;
        }
        
        #pkg-table.collapsed table {
            display: none;
        }
	    #pkg-table .refresh-btn {
            position: absolute;
            top: 5px;
            right: 25px;
            cursor: pointer;
            font-size: 12px;
            background-color: #2226;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 10px;
        }
    </style>

""")

# ╔═╡ 6a10513b-8377-46c5-b56f-47ccb99d51d3
pkg_js = HTML("""
<script>
    window.addEventListener('resize', () => {
        const table = document.getElementById('pkg-table');
        const notebook = document.querySelector('.output_wrapper');
        table.style.top = notebook.offsetTop + 'px';
        table.style.height = notebook.clientHeight + 'px';
    });
    window.dispatchEvent(new Event('resize'));
	
	  function refreshPackageTable() {
	    const cells = document.querySelectorAll('.pluto-cell');
	    cells.forEach(cell => {
	        const codeMirrorInstance = cell.querySelector('.CodeMirror').CodeMirror;
	        const cellContent = codeMirrorInstance.getValue();
	        
	         const regex = new RegExp('using\\\\s+[A-Za-z]+');
	        if (regex.test(cellContent)) {
	            cell.dispatchEvent(new CustomEvent('run-cell'));
	        }
	    });
	}
</script>
""")

# ╔═╡ f0fd90df-a41e-433b-93f6-b5eb7faec823
pkg_table =HTML("""
   $(pkg_css)
   <div id="pkg-table">
        <h3>Package Versions</h3>
        <span class="close-btn" onclick="document.getElementById('pkg-table').classList.toggle('collapsed')">&plus;</span>
	        <button class="refresh-btn" onclick="refreshPackageTable()">Refresh</button>

        <table>
            <tr><th>Package Name</th><th>Version</th></tr>
            $(table_html)
        </table>
    </div>
    $(pkg_js)
""")

# ╔═╡ 00000000-0000-0000-0000-000000000001
PLUTO_PROJECT_TOML_CONTENTS = """
[deps]
Pkg = "44cfe95a-1eb2-52ea-b672-e2afdf69b78f"
PlutoUI = "7f904dfe-b85e-4ff6-b463-dae2292396a8"

[compat]
PlutoUI = "~0.7.50"
"""

# ╔═╡ 00000000-0000-0000-0000-000000000002
PLUTO_MANIFEST_TOML_CONTENTS = """
# This file is machine-generated - editing it directly is not advised

julia_version = "1.8.3"
manifest_format = "2.0"
project_hash = "171264b40c07c79afa29ada01a20d6d6296cdaf0"

[[deps.AbstractPlutoDingetjes]]
deps = ["Pkg"]
git-tree-sha1 = "8eaf9f1b4921132a4cff3f36a1d9ba923b14a481"
uuid = "6e696c72-6542-2067-7265-42206c756150"
version = "1.1.4"

[[deps.ArgTools]]
uuid = "0dad84c5-d112-42e6-8d28-ef12dabb789f"
version = "1.1.1"

[[deps.Artifacts]]
uuid = "56f22d72-fd6d-98f1-02f0-08ddc0907c33"

[[deps.Base64]]
uuid = "2a0f44e3-6c83-55bd-87e4-b1978d98bd5f"

[[deps.ColorTypes]]
deps = ["FixedPointNumbers", "Random"]
git-tree-sha1 = "eb7f0f8307f71fac7c606984ea5fb2817275d6e4"
uuid = "3da002f7-5984-5a60-b8a6-cbb66c0b333f"
version = "0.11.4"

[[deps.CompilerSupportLibraries_jll]]
deps = ["Artifacts", "Libdl"]
uuid = "e66e0078-7015-5450-92f7-15fbd957f2ae"
version = "0.5.2+0"

[[deps.Dates]]
deps = ["Printf"]
uuid = "ade2ca70-3891-5945-98fb-dc099432e06a"

[[deps.Downloads]]
deps = ["ArgTools", "FileWatching", "LibCURL", "NetworkOptions"]
uuid = "f43a241f-c20a-4ad4-852c-f6b1247861c6"
version = "1.6.0"

[[deps.FileWatching]]
uuid = "7b1f6079-737a-58dc-b8bc-7a2ca5c1b5ee"

[[deps.FixedPointNumbers]]
deps = ["Statistics"]
git-tree-sha1 = "335bfdceacc84c5cdf16aadc768aa5ddfc5383cc"
uuid = "53c48c17-4a7d-5ca2-90c5-79b7896eea93"
version = "0.8.4"

[[deps.Hyperscript]]
deps = ["Test"]
git-tree-sha1 = "8d511d5b81240fc8e6802386302675bdf47737b9"
uuid = "47d2ed2b-36de-50cf-bf87-49c2cf4b8b91"
version = "0.0.4"

[[deps.HypertextLiteral]]
deps = ["Tricks"]
git-tree-sha1 = "c47c5fa4c5308f27ccaac35504858d8914e102f9"
uuid = "ac1192a8-f4b3-4bfe-ba22-af5b92cd3ab2"
version = "0.9.4"

[[deps.IOCapture]]
deps = ["Logging", "Random"]
git-tree-sha1 = "f7be53659ab06ddc986428d3a9dcc95f6fa6705a"
uuid = "b5f81e59-6552-4d32-b1f0-c071b021bf89"
version = "0.2.2"

[[deps.InteractiveUtils]]
deps = ["Markdown"]
uuid = "b77e0a4c-d291-57a0-90e8-8db25a27a240"

[[deps.JSON]]
deps = ["Dates", "Mmap", "Parsers", "Unicode"]
git-tree-sha1 = "31e996f0a15c7b280ba9f76636b3ff9e2ae58c9a"
uuid = "682c06a0-de6a-54ab-a142-c8b1cf79cde6"
version = "0.21.4"

[[deps.LibCURL]]
deps = ["LibCURL_jll", "MozillaCACerts_jll"]
uuid = "b27032c2-a3e7-50c8-80cd-2d36dbcbfd21"
version = "0.6.3"

[[deps.LibCURL_jll]]
deps = ["Artifacts", "LibSSH2_jll", "Libdl", "MbedTLS_jll", "Zlib_jll", "nghttp2_jll"]
uuid = "deac9b47-8bc7-5906-a0fe-35ac56dc84c0"
version = "7.84.0+0"

[[deps.LibGit2]]
deps = ["Base64", "NetworkOptions", "Printf", "SHA"]
uuid = "76f85450-5226-5b5a-8eaa-529ad045b433"

[[deps.LibSSH2_jll]]
deps = ["Artifacts", "Libdl", "MbedTLS_jll"]
uuid = "29816b5a-b9ab-546f-933c-edad1886dfa8"
version = "1.10.2+0"

[[deps.Libdl]]
uuid = "8f399da3-3557-5675-b5ff-fb832c97cbdb"

[[deps.LinearAlgebra]]
deps = ["Libdl", "libblastrampoline_jll"]
uuid = "37e2e46d-f89d-539d-b4ee-838fcccc9c8e"

[[deps.Logging]]
uuid = "56ddb016-857b-54e1-b83d-db4d58db5568"

[[deps.MIMEs]]
git-tree-sha1 = "65f28ad4b594aebe22157d6fac869786a255b7eb"
uuid = "6c6e2e6c-3030-632d-7369-2d6c69616d65"
version = "0.1.4"

[[deps.Markdown]]
deps = ["Base64"]
uuid = "d6f4376e-aef5-505a-96c1-9c027394607a"

[[deps.MbedTLS_jll]]
deps = ["Artifacts", "Libdl"]
uuid = "c8ffd9c3-330d-5841-b78e-0817d7145fa1"
version = "2.28.0+0"

[[deps.Mmap]]
uuid = "a63ad114-7e13-5084-954f-fe012c677804"

[[deps.MozillaCACerts_jll]]
uuid = "14a3606d-f60d-562e-9121-12d972cd8159"
version = "2022.2.1"

[[deps.NetworkOptions]]
uuid = "ca575930-c2e3-43a9-ace4-1e988b2c1908"
version = "1.2.0"

[[deps.OpenBLAS_jll]]
deps = ["Artifacts", "CompilerSupportLibraries_jll", "Libdl"]
uuid = "4536629a-c528-5b80-bd46-f80d51c5b363"
version = "0.3.20+0"

[[deps.Parsers]]
deps = ["Dates", "SnoopPrecompile"]
git-tree-sha1 = "478ac6c952fddd4399e71d4779797c538d0ff2bf"
uuid = "69de0a69-1ddd-5017-9359-2bf0b02dc9f0"
version = "2.5.8"

[[deps.Pkg]]
deps = ["Artifacts", "Dates", "Downloads", "LibGit2", "Libdl", "Logging", "Markdown", "Printf", "REPL", "Random", "SHA", "Serialization", "TOML", "Tar", "UUIDs", "p7zip_jll"]
uuid = "44cfe95a-1eb2-52ea-b672-e2afdf69b78f"
version = "1.8.0"

[[deps.PlutoUI]]
deps = ["AbstractPlutoDingetjes", "Base64", "ColorTypes", "Dates", "FixedPointNumbers", "Hyperscript", "HypertextLiteral", "IOCapture", "InteractiveUtils", "JSON", "Logging", "MIMEs", "Markdown", "Random", "Reexport", "URIs", "UUIDs"]
git-tree-sha1 = "5bb5129fdd62a2bbbe17c2756932259acf467386"
uuid = "7f904dfe-b85e-4ff6-b463-dae2292396a8"
version = "0.7.50"

[[deps.Preferences]]
deps = ["TOML"]
git-tree-sha1 = "47e5f437cc0e7ef2ce8406ce1e7e24d44915f88d"
uuid = "21216c6a-2e73-6563-6e65-726566657250"
version = "1.3.0"

[[deps.Printf]]
deps = ["Unicode"]
uuid = "de0858da-6303-5e67-8744-51eddeeeb8d7"

[[deps.REPL]]
deps = ["InteractiveUtils", "Markdown", "Sockets", "Unicode"]
uuid = "3fa0cd96-eef1-5676-8a61-b3b8758bbffb"

[[deps.Random]]
deps = ["SHA", "Serialization"]
uuid = "9a3f8284-a2c9-5f02-9a11-845980a1fd5c"

[[deps.Reexport]]
git-tree-sha1 = "45e428421666073eab6f2da5c9d310d99bb12f9b"
uuid = "189a3867-3050-52da-a836-e630ba90ab69"
version = "1.2.2"

[[deps.SHA]]
uuid = "ea8e919c-243c-51af-8825-aaa63cd721ce"
version = "0.7.0"

[[deps.Serialization]]
uuid = "9e88b42a-f829-5b0c-bbe9-9e923198166b"

[[deps.SnoopPrecompile]]
deps = ["Preferences"]
git-tree-sha1 = "e760a70afdcd461cf01a575947738d359234665c"
uuid = "66db9d55-30c0-4569-8b51-7e840670fc0c"
version = "1.0.3"

[[deps.Sockets]]
uuid = "6462fe0b-24de-5631-8697-dd941f90decc"

[[deps.SparseArrays]]
deps = ["LinearAlgebra", "Random"]
uuid = "2f01184e-e22b-5df5-ae63-d93ebab69eaf"

[[deps.Statistics]]
deps = ["LinearAlgebra", "SparseArrays"]
uuid = "10745b16-79ce-11e8-11f9-7d13ad32a3b2"

[[deps.TOML]]
deps = ["Dates"]
uuid = "fa267f1f-6049-4f14-aa54-33bafae1ed76"
version = "1.0.0"

[[deps.Tar]]
deps = ["ArgTools", "SHA"]
uuid = "a4e569a6-e804-4fa4-b0f3-eef7a1d5b13e"
version = "1.10.1"

[[deps.Test]]
deps = ["InteractiveUtils", "Logging", "Random", "Serialization"]
uuid = "8dfed614-e22c-5e08-85e1-65c5234f0b40"

[[deps.Tricks]]
git-tree-sha1 = "aadb748be58b492045b4f56166b5188aa63ce549"
uuid = "410a4b4d-49e4-4fbc-ab6d-cb71b17b3775"
version = "0.1.7"

[[deps.URIs]]
git-tree-sha1 = "074f993b0ca030848b897beff716d93aca60f06a"
uuid = "5c2747f8-b7ea-4ff2-ba2e-563bfd36b1d4"
version = "1.4.2"

[[deps.UUIDs]]
deps = ["Random", "SHA"]
uuid = "cf7118a7-6976-5b1a-9a39-7adc72f591a4"

[[deps.Unicode]]
uuid = "4ec0a83e-493e-50e2-b9ac-8f72acf5a8f5"

[[deps.Zlib_jll]]
deps = ["Libdl"]
uuid = "83775a58-1f1d-513f-b197-d71354ab007a"
version = "1.2.12+3"

[[deps.libblastrampoline_jll]]
deps = ["Artifacts", "Libdl", "OpenBLAS_jll"]
uuid = "8e850b90-86db-534c-a0d3-1478176c7d93"
version = "5.1.1+0"

[[deps.nghttp2_jll]]
deps = ["Artifacts", "Libdl"]
uuid = "8e850ede-7688-5339-a07c-302acd2aaf8d"
version = "1.48.0+0"

[[deps.p7zip_jll]]
deps = ["Artifacts", "Libdl"]
uuid = "3f19e933-33d8-53b3-aaab-bd5110c3b7a0"
version = "17.4.0+0"
"""

# ╔═╡ Cell order:
# ╠═337c098a-e1fd-4047-9cc5-c6d385d107f2
# ╠═b1691378-534d-4ce3-afc7-1611cb95e6e5
# ╠═5e5e0a55-bc2a-4fc4-aebf-efd8987f7b71
# ╠═e5cf2e05-a2d4-4fec-93d6-a2c27e95380c
# ╠═6a10513b-8377-46c5-b56f-47ccb99d51d3
# ╠═f0fd90df-a41e-433b-93f6-b5eb7faec823
# ╟─00000000-0000-0000-0000-000000000001
# ╟─00000000-0000-0000-0000-000000000002
