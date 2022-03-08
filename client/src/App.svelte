<script>
	import { beforeUpdate, afterUpdate, onMount } from 'svelte';
	import CustomMenu from './ContextMenu/CustomMenu.svelte'; 
	import Cancel from './Icons/Cancel.svelte';
	import CheckCircle from './Icons/CheckCircle.svelte';

	let text_box;
	let random_input;
	let autoscroll;

	let window_checkbox = false;

	let enabled;
	let phrases = [];
	let saved_phrases = [];
	const program_history = 4;
	let last_x_programs = [];
	let last_x_windows = [];
	$: last_programs = window_checkbox ? last_x_windows : last_x_programs;
	let whitelist = []; // an array of strings of process names, e.g. "Discord.exe"
	let currently_open_windows = [];
	let currently_open_processes = [];
	$: open_programs = window_checkbox ? currently_open_windows : currently_open_processes;

	let hovered_phrase;
	let hovered_component;
	let hovered_text;

	let disconnected = false;

	const port = 35465; // defined at top of main.py
	const tt = "http://localhost:".concat(port); // typer translator internal app

	var eventSource = new EventSource('/subscribe');
	eventSource.onmessage = function(m) {
		//console.log(m);
		let data = JSON.parse(m.data);
		switch(data.type) {
			case 'phrase':
				update_phrases(data);
				break;
			case 'program':
				update_program_list(data);
				break;
		}
	}
	eventSource.onerror = function(m) {
		disconnected = true;
	}

	async function get_enable_status() {
		const response = await fetch(tt.concat("/enable"));
		await response.json().then(data => enabled = data.status);
	}

	async function update_enabled(status) {
		const response = await fetch(tt.concat("/enable"), {
			method: "POST",
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				enable: status
			})
		});

		if(!response.ok) {
			alert("Typer translator isn't running! Please check it");
			return;
		}
	}

	function update_phrases(data) {
		phrases = phrases.concat({
			phrase: data.phrase,
			time: data.time,
			timestring: data.timestring,
			tl_phrase: data.tl_phrase
		});
	}

	async function create_program_list() {
		const response = await fetch(tt.concat("/currentprogram"));
		await response.json().then(data => {
			last_x_programs.unshift(data.process); 
			last_x_windows.unshift(data.window);
			last_x_programs = last_x_programs; // svelte reactivity only works on assignment
			last_x_windows = last_x_windows;})
	}

	function update_program_list(data) {
		last_x_programs.unshift(data.process_name);
		last_x_windows.unshift(data.window_name);
		if(last_x_programs.length > program_history) {
			last_x_programs.pop();
			last_x_windows.pop();
		}
		last_x_programs = last_x_programs; // svelte reactivity only works on assignment
		last_x_windows = last_x_windows;
	}

	function remove_phrase(event) {
		let phrase = event.detail;
		phrases = phrases.filter(function(x) {
			return x.time != phrase.time;
		});
	}

	function copy_phrase(event) {
		let text = event.detail;
		navigator.clipboard.writeText(text);
	}
	async function get_saved_phrases() {
		const response = await fetch(tt.concat("/savedphrases"));
		await response.json().then(data => saved_phrases = data);
	}

	async function new_saved_phrase(event) {
		let phrase = event.detail;
		const response = await fetch(tt.concat("/savedphrases"), {
			method: "POST",
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				action: "add",
				phrase: phrase.phrase,
				tl_phrase: phrase.tl_phrase,
			})
		});

		if(!response.ok) {
			alert("Typer translator isn't running! Please check it");
			return;
		}

		// The server needs to store it in the db, and return a json {id, msg, tl_msg}, we need the id if we need to delete
		await response.json().then(data => saved_phrases = saved_phrases.concat(data)); 
	}

	async function remove_saved_phrase(event) {
		let phrase = event.detail;
		const response = await fetch(tt.concat("/savedphrases"), {
			method: "POST",
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				action: "remove",
				id: phrase.id
			})
		});

		if(!response.ok) {
			alert("Typer translator isn't running! Please check it");
			return;
		}

		saved_phrases = saved_phrases.filter(function(x) {
			return x.id != phrase.id;
		});
	}	

	async function get_whitelist_data() {
		const response = await fetch(tt.concat("/whitelist"));
		await response.json().then(data => {whitelist = data});
	}

	async function get_open_windows() {
		const response = await fetch(tt.concat("/programs"));
		await response.json().then(data => {currently_open_processes = data.processes; currently_open_windows = data.windows});
	}

	async function add_to_whitelist(window) {
		const response = await fetch(tt.concat("/whitelist"), {
			method: "POST",
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				action: "add",
				program: window
			})
		});

		if(!response.ok) {
			alert("Typer translator isn't running! Please check it");
			return;
		}

		// The server needs to store it in the db, and return a json {id, msg, tl_msg}, we need the id if we need to delete
		whitelist = whitelist.concat(window); 
	}

	async function remove_from_whitelist(window) {
		const response = await fetch(tt.concat("/whitelist"), {
			method: "POST",
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				action: "remove",
				program: window
			})
		});

		if(!response.ok) {
			alert("Typer translator isn't running! Please check it");
			return;
		}

		// The server needs to store it in the db, and return a json {id, msg, tl_msg}, we need the id if we need to delete
		whitelist = whitelist.filter(function(x) {
			return x != window;
		});
	}

	function handle_keypress(event) {
		if(event.keyCode == 13) { // on enter
			event.preventDefault();
			random_input.value = "";
		}
	}

	function setHoveredInfo(component, phrase, text) {
		hovered_component = component;
		hovered_phrase = phrase;
		hovered_text = text;
	}

	function unsetHoveredInfo() {
		hovered_component = "";
		hovered_phrase = {};
		hovered_text = "";
	}
	
	beforeUpdate(() => {
		autoscroll = text_box && (text_box.offsetHeight + text_box.scrollTop) > (text_box.scrollHeight - 20);
	});

	afterUpdate(() => {
		if (autoscroll) text_box.scrollTo(0, text_box.scrollHeight);
	});

	onMount(() => {
		get_enable_status();
		get_saved_phrases();
		get_whitelist_data();
		create_program_list();
		get_open_windows();
	})
</script>

<svelte:window on:keydown={() => random_input.focus()}/>

<div class="chat">
	<div class="row">
		<div class="column" style="flex: 1;">
			<h1>Settings</h1>
			<span class={disconnected ? 'connectivity-no' : enabled ? 'connectivity-yes' : 'connectivity-disabled'}>
				{#if disconnected}
					Disconnected! Please refresh page or check the app!
				{:else if !enabled}
					Disabled!
				{:else}
					Connected
				{/if}
			</span>
			<div>
				<span>
					<label class="switch">
						<input type="checkbox" bind:checked={enabled} on:change={update_enabled(enabled)}>
						<span class="slider round"></span>
					</label>
				</span>
				<span class="sp-window-text">
					Typer Translator {#if enabled}On!{:else}Off!{/if}
				</span>
			</div>
			<h2 style='margin: 0px'>Allowed Programs</h2>
			<div>
				<span>
					<label class="switch">
						<input type="checkbox" bind:checked={window_checkbox}>
						<span class="slider round"></span>
					</label>
				</span>
				<span class="sp-window-text">
					Show specific windows
				</span>
			</div>
			<h3 style='margin-top: 10px; margin-bottom: 5px'>Last 4 {#if window_checkbox}Windows{:else}Programs{/if} (You were in)</h3>
			{#each last_programs as program, i} 
				<p class="last_program">{#if i == 0}🡆{/if} {program}</p>
			{/each}
			<button style="margin-top: 5px" on:click={() => {get_open_windows()}}>Refresh</button>
			<div class="scrollable">
				{#each open_programs as window}
				<!-- These should just be strings of the process names -->
				<div style='margin-top: 3px; margin-bottom: 3px'>
					<span class={whitelist.includes(window) ? 'whitelisted' : 'not-whitelisted'}>
						<span style='padding: 0'>
							{#if whitelist.includes(window)}
								<button class="whitelist-button" on:click={() => {remove_from_whitelist(window)}}>
									<CheckCircle />
								</button>
							{:else}	
								<button class="whitelist-button" on:click={() => {add_to_whitelist(window)}}>
									<Cancel />
								</button>
							{/if}
						</span>
						<span class="whitelist-program">
							{window}
						</span>
					</span>
				</div>
				{/each}
			</div>
		</div>
		<div class="column" style="flex: 3">
			<div class="scrollable" bind:this={text_box}>
				{#each phrases as phrase, i}
				<!-- To reduce the time stamp spam, only show a new timestamp if it takes more than 10 seconds between a msg -->
					{#if i > 0}
						{#if phrase.time - phrases[i-1].time > 10} 
						<article class="time">
							<span>{phrase.timestring}</span>
						</article>
						{/if}
					{:else}
						<article class="time">
							<span>{phrase.timestring}</span>
						</article>
					{/if}
					<article class="author">
						<span on:mouseleave={() => unsetHoveredInfo()}
							  on:mouseenter={() => setHoveredInfo("phrases", phrase, phrase.phrase)}
							 >
							{phrase.phrase}
						</span>
					</article>
					<article class="translator">
						<span on:mouseleave={() => unsetHoveredInfo()}
							  on:mouseenter={() => setHoveredInfo("phrases", phrase, phrase.tl_phrase)}
							  >
							{phrase.tl_phrase}
						</span>
					</article>
				{/each}
			</div>
		</div>
		<div class="column" style="flex: 1;">
			<h1>Just a text box so you can type</h1>
			<br>
			<textarea class="random_input" type="text" on:keypress={handle_keypress} bind:this={random_input}/>
			<br>
			<h1>Saved Phrases</h1>
			<div class="scrollable">
				{#each saved_phrases as saved}
					<article class="saved_phrase" on:mouseenter={() => setHoveredInfo("saved_phrases", saved, saved.tl_phrase)}>
						<span class="saved_text"
						 on:mouseleave={() => unsetHoveredInfo()} 
						 on:mouseenter={() => setHoveredInfo("saved_phrases", saved, saved.phrase)} 
						 >
							{saved.phrase}
						</span>
						<br>
						<span class="saved_translated" 
						 on:mouseleave={() => unsetHoveredInfo()} 
						 on:mouseenter={() => setHoveredInfo("saved_phrases", saved, saved.tl_phrase)} 
						 >
							{saved.tl_phrase}
						</span>
					</article>
					<br>
				{/each}
			</div>
		</div>
	</div>
</div>

<CustomMenu
	hovered_component={hovered_component}
	hovered_phrase={hovered_phrase}
	hovered_text={hovered_text}
	on:save-phrase={new_saved_phrase}
	on:copy-phrase={copy_phrase}
	on:delete-phrase={remove_phrase}
	on:delete-saved-phrase={remove_saved_phrase}
	/>


<style>
	h1, h2, h3 {
		text-align: center;
	}

	.last_program {
		text-align: center;
		margin: 0;
	}

	.saved_phrase {
		background-color: #262a2b;
		border-radius: 1em 1em 1em 1em;
		border: 1px solid rgb(45, 45, 45);
		width: 80%;
		display: table;
    	margin: 0 auto;
	}

	.saved_text,
	.saved_translated {
		font-size: large;
		color: white;
		background-color: rgb(60, 60, 60);
		border-radius: 1em 1em 1em 1em;
		border: 1px solid rgb(45, 45, 45);
		max-width: 90%;
		display: table;
		margin: 0 auto;
	}

	.saved_text:hover,
	.saved_translated:hover {
		background-color: rgb(53, 53, 53);
	}

	.whitelist-program {
		max-width: 60%;
		vertical-align: middle;
		word-break: break-all;
	}

	.whitelist-button {
		margin: 0;
		background-color: transparent;
		border: 0;
		height: 64px;
		width: 64px;
		cursor: pointer;
		vertical-align: middle;
	}

	.whitelisted,
	.not-whitelisted {
		font-size: larger;
		background-color: #262a2b;
		border-radius: 1em 1em 1em 1em;
		border: 1px solid rgb(45, 45, 45);
		width: 80%;
		height: 64px;
		display: table;
    	margin: 0 auto;
	}

	.whitelisted {
		color: gold;
	}

	.not-whitelisted {
		color: lightslategray;
	}

	.connectivity-disabled {
		text-align: center;
		color: black;
		background-color: gold;
	}

	.connectivity-yes {
		text-align: center;
		background-color: green;
	}

	.connectivity-no {
		text-align: center;
		background-color: darkred;
	}

	.random_input {
		min-height: 30%;
		max-height: 30%;
		width: 90%;
		align-self: center;
		word-break: break-all;
		overflow-y: auto;
	}

	.chat {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
		margin: 0 0 0 0;
		padding: 0 0 0 0;
	}

	.scrollable {
		flex: 1 1 auto;
		/* border-top: 1px solid #eee; */
		margin: 0 0 0 0;
		overflow-y: auto;
	}

	article {
		margin: 0.5em 0;
	}

	.author {
		text-align: right;
	}

	.time {
		text-align: center;
	}

	span {
		padding: 0.5em 1em;
		display: inline-block;
	}

	.time span {
		font-size: small;
		background-color: grey;
		border-radius: 1em 1em 1em 1em;
		color: #eee;
	}

	.translator span {
		font-size: medium;
		color: #eee;
		background-color: #595d61;
		border-radius: 1em 1em 1em 0;
		transform: translateX(3vw);
	}

	.author span {
		font-size: medium;
		background-color: #0074D9;
		color: white;
		border-radius: 1em 1em 0 1em;
		word-break: break-all;
		transform: translateX(-3vw);
	}

	.author span:hover {
		background-color: #015094;
	}

	.translator span:hover {
		background-color: #494b4d;
	}

	.row {
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		width: 100%;
		height: 100%
	}

	.column {
		display: flex;
		flex-direction: column;
		flex-basis: 100%;
		height: 100%;
		margin: 0 0 0 0;
		padding: 0 0 0 0;
		border-left: 1px solid rgb(100, 100, 100);
		border-right: 1px solid rgb(100, 100, 100);
	}

	.sp-window-text {
		font-size: large;
		margin: 0 auto;
	}

	.switch {
		position: relative;
		display: inline-block;
		width: 60px;
		height: 34px;
	}

	/* Hide default HTML checkbox */
	.switch input {
		opacity: 0;
		width: 0;
		height: 0;
	}

	/* The slider */
	.slider {
		position: absolute;
		cursor: pointer;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: #ccc;
		-webkit-transition: .4s;
		transition: .4s;
	}

	.slider:before {
		position: absolute;
		content: "";
		height: 26px;
		width: 26px;
		left: 4px;
		bottom: 4px;
		background-color: white;
		-webkit-transition: .4s;
		transition: .4s;
	}

	input:checked + .slider {
		background-color: #2196F3;
	}

	input:focus + .slider {
		box-shadow: 0 0 1px #2196F3;
	}

	input:checked + .slider:before {
		-webkit-transform: translateX(26px);
		-ms-transform: translateX(26px);
		transform: translateX(26px);
	}

	/* Rounded sliders */
	.slider.round {
		border-radius: 34px;
	}

	.slider.round:before {
		border-radius: 50%;
	}
</style>