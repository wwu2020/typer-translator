<script>
	import { beforeUpdate, afterUpdate } from 'svelte';

	let div;
	let autoscroll;
	let phrases = [];

	var eventSource = new EventSource('/subscribe');
	eventSource.onmessage = function(m) {
		console.log(m);
		let data = JSON.parse(m.data);
		phrases = phrases.concat({
			text: data.text,
			translator: data.translator,
			translated: data.translated
		});
	}
	// function post(url, data) {
	// 	var request = new XMLHttpRequest();
	// 	request.open('POST', url, true);
	// 	request.setRequestHeader('Content-Type', 'text/plain; charset=UTF-8');
	// 	request.send(data);
	// }
	// function publish() {
	// 	var message = document.getElementById("msg").value;
	// 	post('/publish', message);
	// }

	
	beforeUpdate(() => {
		autoscroll = div && (div.offsetHeight + div.scrollTop) > (div.scrollHeight - 20);
	});

	afterUpdate(() => {
		if (autoscroll) div.scrollTo(0, div.scrollHeight);
	});
</script>
<form action="http://localhost:5000/shutdown">
    <input type="submit" value="Shutdown" />
</form>

<div class="chat">
	<div class="scrollable" bind:this={div}>
		{#each phrases as phrase}
			<article class="author">
				<span>{phrase.text}</span>
			</article>
			<article class="translator">
				<span>{phrase.translated}</span>
			</article>
		{/each}
	</div>
</div>


<style>
	.chat {
		display: flex;
		flex-direction: column;
		height: 100%;
		max-width: 320px;
	}

	.scrollable {
		flex: 1 1 auto;
		border-top: 1px solid #eee;
		margin: 0 0 0.5em 0;
		overflow-y: auto;
	}

	article {
		margin: 0.5em 0;
	}

	.author {
		text-align: right;
	}

	span {
		padding: 0.5em 1em;
		display: inline-block;
	}

	.translator span {
		background-color: #eee;
		border-radius: 1em 1em 1em 0;
	}

	.author span {
		background-color: #0074D9;
		color: white;
		border-radius: 1em 1em 0 1em;
		word-break: break-all;
	}
</style>