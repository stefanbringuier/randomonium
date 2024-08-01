### A Pluto.jl notebook ###
# v0.19.25

#> [frontmatter]
#> author = "Stefan Bringuier"
#> title = "ChatGPT in Pluto"
#> date = "2023-05-19"
#> tags = ["AI", "Chatbot"]
#> description = "Using ReplGPT.jl to interface with ChatGPT"
#> license = "CC-BY-4.0"

using Markdown
using InteractiveUtils

# This Pluto notebook uses @bind for interactivity. When running this notebook outside of Pluto, the following 'mock version' of @bind gives bound variables a default value (instead of an error).
macro bind(def, element)
    quote
        local iv = try Base.loaded_modules[Base.PkgId(Base.UUID("6e696c72-6542-2067-7265-42206c756150"), "AbstractPlutoDingetjes")].Bonds.initial_value catch; b -> missing; end
        local el = $(esc(element))
        global $(esc(def)) = Core.applicable(Base.get, el) ? Base.get(el) : iv(el)
        el
    end
end

# ╔═╡ 08cb98d6-f604-11ed-2225-fd5481b32d3a
using ReplGPT

# ╔═╡ 8e0971f0-3f5c-4f3d-a332-c3fa6727cc26
using OpenAI

# ╔═╡ 1da4225a-029f-4f54-bee8-d79df4c67061
begin
	using PlutoUI
	using Test
end

# ╔═╡ 766d9059-806d-48ae-a465-c440f099b72a
md"""
# GPT in Pluto
**Author: Stefan Bringuier**

My bet is that Pluto.jl will get some kind of [native support](https://juliapluto.github.io/weekly-call-notes/2023/03-28/notes.html) for access to an LLM to ask Julia questions, but for now, we can use the [ReplGPT.jl]() package or even just use the [OpenAI.jl]() wrapper itself to customize it for your notebooks.

I'm just going to use the ReplGPT.jl package. It is pretty straightforward, first include the package, then also use the `PasswordField` from PlutoUI.jl to paste your OpenAI API key and set your API key.
"""

# ╔═╡ 01e3049f-9f46-4a9f-b745-5d889ef6c130
md"""
OpenAI API Key: $(@bind api_key PasswordField())
"""

# ╔═╡ 8bed0b5e-60ad-42a8-982a-c82cfcc63146
if !isempty(api_key)
	ReplGPT.setAPIkey(api_key)
end

# ╔═╡ 5acc0d72-3d0c-4564-baa0-9e4b1dc76925
md"""
Now if you want, you can create a text box with PlutoUI tools to submit a query and bind it to a variable called `message`. It's not really necessary but looks and feels nice.
"""

# ╔═╡ 30ce9c08-b65a-49cd-9d30-abf99aa90b57
@bind message confirm(TextField((82,10),default="Your ChatGPT question"))

# ╔═╡ d1d6a203-acc8-485b-b93d-17bfeca53b62
md"""
As mentioned above the textbox above is just a stylistic choice but more practical usage would be to just call `ReplGPT.call_chatgpt(message)` as needed in your notebook. This provides the response in markdown. So you can just keep calling this method with whatever messages you want.
### ChatGPT Response
"""

# ╔═╡ 0c9cb7bb-0f70-46a0-8e6b-f02a887795b0
begin
	if message != "Your ChatGPT question" 
		response = ReplGPT.call_chatgpt(message)
	end
end

# ╔═╡ 8cf33299-ecfd-41a8-b089-b2d59b3e3307
md"""
## Usage
Its a bit slow so using the the ChatGPT UI or other AI-powered resources is probably more practical, but what would really be cool is if you condition the prompt and check the response such that you only get the Julia code, with no irrelevant text other than valid Julia and comments. Then that code gets run in a cell. Basically your write code directly to a Pluto cell and running it.

Going to try this, below. But using the OpenAI.jl wrapper.
"""

# ╔═╡ 53110326-8869-4280-9b4e-e2757005524e
md"""
## OpenAI.jl + Pluto.jl → Hermes 

With `ReplGPT` you don't have to worry about anything other than your API key and the message. But you as I mentioned in the previous paragraph, what if you want to do something dangerous but powerful like inject code into a pluto cell and run? You can do this by using `OpenAI.jl` wrapper. 

For fun, I'm going to call this functionality `Hermes` after the Greek diety who was the messenger amongst the other dieties. Thus `Hermes` will deliver information to us in Pluto.
"""

# ╔═╡ 66439cad-fc56-4f74-80f7-12627ed6125e
md"""
!!! note "Conditioning ChatGPT"
	We need to condition ChatGPT otherwise to give us just valid Julia code text only. Otherwise we will get all the text that describes or summarizes the response. This works most of the time but there are no gaurentees, so probably a more systematic was of doing it is to also include a function all to a `formatter` which only grabs the code in markdown code fencing in the repsonse.

"""

# ╔═╡ 7293c071-e8d9-442b-8dc6-aea6f268f7f5
macro hermes_str(prompt)
	model = "gpt-3.5-turbo"
	context = """
		You are a Julia programmer who develops exclusively in Pluto.jl environment.  Your responses MUST ONLY SHOW raw Julia code, docstrings, or Julia comments. Do NOT include any summaries or explanations. DO NOT format the response as Markdown. DO NOT use code fencing or code markup, ONLY show valid raw text valid in Julia. Docstrings should be concise. Here is your prompt: \n
	"""
	if !isempty(api_key)
		result = create_chat(
	    	api_key, 
	    	model,
	    	[Dict("role" => "user", "content"=> context*prompt)]
	  	)
	else
		return "OpenAI API key is not set"
	end
	response_str = result.response[:choices][begin][:message][:content]
	eval(Meta.parse(response_str))
end


# ╔═╡ 4e588a51-6bad-4a72-9a2b-5c8c1596bb4c
hermes"""Create a function for the trapizodial rule"""

# ╔═╡ fa86d555-13b8-4f3b-8264-e4b0654bf7fd
md"""
Pretty cool! It runs the code returned by ChatGPT. What's nice is it also returned the function docstring so you know how to use it. But we don't know if it's correct so probably want a test. I'm going to actually ask ChatGPT to create the test.
"""

# ╔═╡ ffc4a4f3-b6d5-4aad-9947-f596c619e815
begin
	doc_info = @doc trap_rule;
	doc_str = doc_info.content[1]
end;

# ╔═╡ 438cb654-c686-459f-b88d-7ed8a06ea4a4
hermes"""Please write tests for the following function:\n $(doc_str)\n You can test the functions exp, sin, and cos with tolerance 1.0e-3."""

# ╔═╡ f758294e-f55a-48df-bee3-8dbb7c4dd56c
md"""
!!! error 
	The request above generate tests from the docstring using `hermes` seems to  fail a lot, both in request and design(?), so in this instance it is probably easier to go back to `ReplGPT` and see what it gives.
"""

# ╔═╡ b799cc17-5b08-4a2e-b023-bfa2cead5c4e
md"""
Lets try out the tests. I asked for a tolerance of 1.0e-3 but I'll make this adjustable. I also didn't indicate the number of points, so I'll make this a slider too.
"""

# ╔═╡ 37b9d235-208e-4e47-85a9-75425190c020
md"""
tolerance: $(@bind atol Slider(10.0 .^ range(-6, stop=-2, step=1),default=1.0e-3,show_value=true))

points: $(@bind points Slider(10 .^ range(1,stop=3,step=1),default=10^2,show_value=true))
"""

# ╔═╡ 4c0a215f-9034-43e7-96c9-9d4a692a334c
@test isapprox(trap_rule(exp, 0, 1, points), exp(1) - 1, atol=atol)

# ╔═╡ 840b0ec9-4b79-429a-9c87-590f1cb5fbd8
@test isapprox(trap_rule(sin, 0, pi, points), 2, atol=atol)

# ╔═╡ 07516de2-cc77-41fe-9614-c007786c3d53
@test isapprox(trap_rule(cos, 0, pi/2, points), 1, atol=atol)

# ╔═╡ 44c78a22-6df8-45cc-9950-6818bde73e63
md"""
So they pass with the tolerance and number of points set to 1.0e-3 and 100. If you adjust these some function test will fail.
"""

# ╔═╡ f1976aec-a533-46ba-9bf7-753bfd858df3
md"""
## Additional Packages
"""

# ╔═╡ 61fa1153-9204-4745-8cef-d1f3080edfd6
TableOfContents(title="🤖 GPT Models in Pluto")

# ╔═╡ 00000000-0000-0000-0000-000000000001
PLUTO_PROJECT_TOML_CONTENTS = """
[deps]
OpenAI = "e9f21f70-7185-4079-aca2-91159181367c"
PlutoUI = "7f904dfe-b85e-4ff6-b463-dae2292396a8"
ReplGPT = "8ef5fce9-1516-4e06-b171-18cb54ddb04b"
Test = "8dfed614-e22c-5e08-85e1-65c5234f0b40"

[compat]
OpenAI = "~0.8.4"
PlutoUI = "~0.7.51"
ReplGPT = "~0.3.0"
"""

# ╔═╡ 00000000-0000-0000-0000-000000000002
PLUTO_MANIFEST_TOML_CONTENTS = """
# This file is machine-generated - editing it directly is not advised

julia_version = "1.9.0"
manifest_format = "2.0"
project_hash = "1cf41ad201609e5734d40001316db638597270b6"

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

[[deps.BitFlags]]
git-tree-sha1 = "43b1a4a8f797c1cddadf60499a8a077d4af2cd2d"
uuid = "d1d4a3ce-64b1-5f1a-9ba4-7e7e69966f35"
version = "0.1.7"

[[deps.CodecZlib]]
deps = ["TranscodingStreams", "Zlib_jll"]
git-tree-sha1 = "9c209fb7536406834aa938fb149964b985de6c83"
uuid = "944b1d66-785c-5afd-91f1-9de20f533193"
version = "0.7.1"

[[deps.ColorTypes]]
deps = ["FixedPointNumbers", "Random"]
git-tree-sha1 = "eb7f0f8307f71fac7c606984ea5fb2817275d6e4"
uuid = "3da002f7-5984-5a60-b8a6-cbb66c0b333f"
version = "0.11.4"

[[deps.CompilerSupportLibraries_jll]]
deps = ["Artifacts", "Libdl"]
uuid = "e66e0078-7015-5450-92f7-15fbd957f2ae"
version = "1.0.2+0"

[[deps.ConcurrentUtilities]]
deps = ["Serialization", "Sockets"]
git-tree-sha1 = "96d823b94ba8d187a6d8f0826e731195a74b90e9"
uuid = "f0e56b4a-5159-44fe-b623-3e5288b988bb"
version = "2.2.0"

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

[[deps.HTTP]]
deps = ["Base64", "CodecZlib", "ConcurrentUtilities", "Dates", "Logging", "LoggingExtras", "MbedTLS", "NetworkOptions", "OpenSSL", "Random", "SimpleBufferStream", "Sockets", "URIs", "UUIDs"]
git-tree-sha1 = "877b7bc42729aa2c90bbbf5cb0d4294bd6d42e5a"
uuid = "cd3eb016-35fb-5094-929b-558a96fad6f3"
version = "1.9.1"

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

[[deps.JLLWrappers]]
deps = ["Preferences"]
git-tree-sha1 = "abc9885a7ca2052a736a600f7fa66209f96506e1"
uuid = "692b3bcd-3c85-4b1f-b108-f13ce0eb3210"
version = "1.4.1"

[[deps.JSON]]
deps = ["Dates", "Mmap", "Parsers", "Unicode"]
git-tree-sha1 = "31e996f0a15c7b280ba9f76636b3ff9e2ae58c9a"
uuid = "682c06a0-de6a-54ab-a142-c8b1cf79cde6"
version = "0.21.4"

[[deps.JSON3]]
deps = ["Dates", "Mmap", "Parsers", "SnoopPrecompile", "StructTypes", "UUIDs"]
git-tree-sha1 = "84b10656a41ef564c39d2d477d7236966d2b5683"
uuid = "0f8b85d8-7281-11e9-16c2-39a750bddbf1"
version = "1.12.0"

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
deps = ["Libdl", "OpenBLAS_jll", "libblastrampoline_jll"]
uuid = "37e2e46d-f89d-539d-b4ee-838fcccc9c8e"

[[deps.Logging]]
uuid = "56ddb016-857b-54e1-b83d-db4d58db5568"

[[deps.LoggingExtras]]
deps = ["Dates", "Logging"]
git-tree-sha1 = "cedb76b37bc5a6c702ade66be44f831fa23c681e"
uuid = "e6f89c97-d47a-5376-807f-9c37f3926c36"
version = "1.0.0"

[[deps.MIMEs]]
git-tree-sha1 = "65f28ad4b594aebe22157d6fac869786a255b7eb"
uuid = "6c6e2e6c-3030-632d-7369-2d6c69616d65"
version = "0.1.4"

[[deps.Markdown]]
deps = ["Base64"]
uuid = "d6f4376e-aef5-505a-96c1-9c027394607a"

[[deps.MbedTLS]]
deps = ["Dates", "MbedTLS_jll", "MozillaCACerts_jll", "Random", "Sockets"]
git-tree-sha1 = "03a9b9718f5682ecb107ac9f7308991db4ce395b"
uuid = "739be429-bea8-5141-9913-cc70e7f3736d"
version = "1.1.7"

[[deps.MbedTLS_jll]]
deps = ["Artifacts", "Libdl"]
uuid = "c8ffd9c3-330d-5841-b78e-0817d7145fa1"
version = "2.28.2+0"

[[deps.Mmap]]
uuid = "a63ad114-7e13-5084-954f-fe012c677804"

[[deps.MozillaCACerts_jll]]
uuid = "14a3606d-f60d-562e-9121-12d972cd8159"
version = "2022.10.11"

[[deps.NetworkOptions]]
uuid = "ca575930-c2e3-43a9-ace4-1e988b2c1908"
version = "1.2.0"

[[deps.OpenAI]]
deps = ["Dates", "HTTP", "JSON3"]
git-tree-sha1 = "23ec0ca2f59b8f18309794028e8f6a811f95e96a"
uuid = "e9f21f70-7185-4079-aca2-91159181367c"
version = "0.8.4"

[[deps.OpenBLAS_jll]]
deps = ["Artifacts", "CompilerSupportLibraries_jll", "Libdl"]
uuid = "4536629a-c528-5b80-bd46-f80d51c5b363"
version = "0.3.21+4"

[[deps.OpenSSL]]
deps = ["BitFlags", "Dates", "MozillaCACerts_jll", "OpenSSL_jll", "Sockets"]
git-tree-sha1 = "51901a49222b09e3743c65b8847687ae5fc78eb2"
uuid = "4d8831e6-92b7-49fb-bdf8-b643e874388c"
version = "1.4.1"

[[deps.OpenSSL_jll]]
deps = ["Artifacts", "JLLWrappers", "Libdl"]
git-tree-sha1 = "6cc6366a14dbe47e5fc8f3cbe2816b1185ef5fc4"
uuid = "458c3c95-2e84-50aa-8efc-19380b2a3a95"
version = "3.0.8+0"

[[deps.Parsers]]
deps = ["Dates", "PrecompileTools", "UUIDs"]
git-tree-sha1 = "7302075e5e06da7d000d9bfa055013e3e85578ca"
uuid = "69de0a69-1ddd-5017-9359-2bf0b02dc9f0"
version = "2.5.9"

[[deps.Pkg]]
deps = ["Artifacts", "Dates", "Downloads", "FileWatching", "LibGit2", "Libdl", "Logging", "Markdown", "Printf", "REPL", "Random", "SHA", "Serialization", "TOML", "Tar", "UUIDs", "p7zip_jll"]
uuid = "44cfe95a-1eb2-52ea-b672-e2afdf69b78f"
version = "1.9.0"

[[deps.PlutoUI]]
deps = ["AbstractPlutoDingetjes", "Base64", "ColorTypes", "Dates", "FixedPointNumbers", "Hyperscript", "HypertextLiteral", "IOCapture", "InteractiveUtils", "JSON", "Logging", "MIMEs", "Markdown", "Random", "Reexport", "URIs", "UUIDs"]
git-tree-sha1 = "b478a748be27bd2f2c73a7690da219d0844db305"
uuid = "7f904dfe-b85e-4ff6-b463-dae2292396a8"
version = "0.7.51"

[[deps.PrecompileTools]]
deps = ["Preferences"]
git-tree-sha1 = "259e206946c293698122f63e2b513a7c99a244e8"
uuid = "aea7be01-6a6a-4083-8856-8a6e6704d82a"
version = "1.1.1"

[[deps.Preferences]]
deps = ["TOML"]
git-tree-sha1 = "7eb1686b4f04b82f96ed7a4ea5890a4f0c7a09f1"
uuid = "21216c6a-2e73-6563-6e65-726566657250"
version = "1.4.0"

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

[[deps.ReplGPT]]
deps = ["Markdown", "OpenAI", "Preferences", "ReplMaker"]
git-tree-sha1 = "25b346180fa2e5d195f45ab9111cc83873be6415"
uuid = "8ef5fce9-1516-4e06-b171-18cb54ddb04b"
version = "0.3.0"

[[deps.ReplMaker]]
deps = ["REPL", "Unicode"]
git-tree-sha1 = "f8bb680b97ee232c4c6591e213adc9c1e4ba0349"
uuid = "b873ce64-0db9-51f5-a568-4457d8e49576"
version = "0.2.7"

[[deps.SHA]]
uuid = "ea8e919c-243c-51af-8825-aaa63cd721ce"
version = "0.7.0"

[[deps.Serialization]]
uuid = "9e88b42a-f829-5b0c-bbe9-9e923198166b"

[[deps.SimpleBufferStream]]
git-tree-sha1 = "874e8867b33a00e784c8a7e4b60afe9e037b74e1"
uuid = "777ac1f9-54b0-4bf8-805c-2214025038e7"
version = "1.1.0"

[[deps.SnoopPrecompile]]
deps = ["Preferences"]
git-tree-sha1 = "e760a70afdcd461cf01a575947738d359234665c"
uuid = "66db9d55-30c0-4569-8b51-7e840670fc0c"
version = "1.0.3"

[[deps.Sockets]]
uuid = "6462fe0b-24de-5631-8697-dd941f90decc"

[[deps.SparseArrays]]
deps = ["Libdl", "LinearAlgebra", "Random", "Serialization", "SuiteSparse_jll"]
uuid = "2f01184e-e22b-5df5-ae63-d93ebab69eaf"

[[deps.Statistics]]
deps = ["LinearAlgebra", "SparseArrays"]
uuid = "10745b16-79ce-11e8-11f9-7d13ad32a3b2"
version = "1.9.0"

[[deps.StructTypes]]
deps = ["Dates", "UUIDs"]
git-tree-sha1 = "ca4bccb03acf9faaf4137a9abc1881ed1841aa70"
uuid = "856f2bd8-1eba-4b0a-8007-ebc267875bd4"
version = "1.10.0"

[[deps.SuiteSparse_jll]]
deps = ["Artifacts", "Libdl", "Pkg", "libblastrampoline_jll"]
uuid = "bea87d4a-7f5b-5778-9afe-8cc45184846c"
version = "5.10.1+6"

[[deps.TOML]]
deps = ["Dates"]
uuid = "fa267f1f-6049-4f14-aa54-33bafae1ed76"
version = "1.0.3"

[[deps.Tar]]
deps = ["ArgTools", "SHA"]
uuid = "a4e569a6-e804-4fa4-b0f3-eef7a1d5b13e"
version = "1.10.0"

[[deps.Test]]
deps = ["InteractiveUtils", "Logging", "Random", "Serialization"]
uuid = "8dfed614-e22c-5e08-85e1-65c5234f0b40"

[[deps.TranscodingStreams]]
deps = ["Random", "Test"]
git-tree-sha1 = "9a6ae7ed916312b41236fcef7e0af564ef934769"
uuid = "3bb67fe8-82b1-5028-8e26-92a6c54297fa"
version = "0.9.13"

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
version = "1.2.13+0"

[[deps.libblastrampoline_jll]]
deps = ["Artifacts", "Libdl"]
uuid = "8e850b90-86db-534c-a0d3-1478176c7d93"
version = "5.7.0+0"

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
# ╟─766d9059-806d-48ae-a465-c440f099b72a
# ╠═08cb98d6-f604-11ed-2225-fd5481b32d3a
# ╟─01e3049f-9f46-4a9f-b745-5d889ef6c130
# ╠═8bed0b5e-60ad-42a8-982a-c82cfcc63146
# ╟─5acc0d72-3d0c-4564-baa0-9e4b1dc76925
# ╟─30ce9c08-b65a-49cd-9d30-abf99aa90b57
# ╟─d1d6a203-acc8-485b-b93d-17bfeca53b62
# ╠═0c9cb7bb-0f70-46a0-8e6b-f02a887795b0
# ╟─8cf33299-ecfd-41a8-b089-b2d59b3e3307
# ╟─53110326-8869-4280-9b4e-e2757005524e
# ╠═8e0971f0-3f5c-4f3d-a332-c3fa6727cc26
# ╟─66439cad-fc56-4f74-80f7-12627ed6125e
# ╠═7293c071-e8d9-442b-8dc6-aea6f268f7f5
# ╠═4e588a51-6bad-4a72-9a2b-5c8c1596bb4c
# ╟─fa86d555-13b8-4f3b-8264-e4b0654bf7fd
# ╠═ffc4a4f3-b6d5-4aad-9947-f596c619e815
# ╠═438cb654-c686-459f-b88d-7ed8a06ea4a4
# ╟─f758294e-f55a-48df-bee3-8dbb7c4dd56c
# ╟─b799cc17-5b08-4a2e-b023-bfa2cead5c4e
# ╟─37b9d235-208e-4e47-85a9-75425190c020
# ╠═4c0a215f-9034-43e7-96c9-9d4a692a334c
# ╠═840b0ec9-4b79-429a-9c87-590f1cb5fbd8
# ╠═07516de2-cc77-41fe-9614-c007786c3d53
# ╟─44c78a22-6df8-45cc-9950-6818bde73e63
# ╟─f1976aec-a533-46ba-9bf7-753bfd858df3
# ╠═1da4225a-029f-4f54-bee8-d79df4c67061
# ╠═61fa1153-9204-4745-8cef-d1f3080edfd6
# ╟─00000000-0000-0000-0000-000000000001
# ╟─00000000-0000-0000-0000-000000000002
