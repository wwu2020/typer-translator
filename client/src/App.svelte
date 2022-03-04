<script>
	import { beforeUpdate, afterUpdate } from 'svelte';

	let div;
	let autoscroll;
	let phrases = [];

	var eventSource = new EventSource('/subscribe');
	eventSource.onmessage = function(m) {
		//console.log(m);
		let data = JSON.parse(m.data);
		phrases = phrases.concat({
			text: data.text,
			time: data.time,
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
<!-- <form action="http://localhost:5000/shutdown">
    <input type="submit" value="Shutdown" />
</form> -->

<div class="chat">
	<div class="row">
		<div class="column" style="flex: 1;">
			<h1>Settings</h1>
			<br>
		</div>
		<div class="column" style="flex: 3">
			<div class="scrollable" bind:this={div}>
				{#each phrases as phrase}
					<article class="time">
						<span>{phrase.time}</span>
					</article>
					<article class="author">
						<span>{phrase.text}</span>
					</article>
					<article class="translator">
						<span>{phrase.translated}</span>
					</article>
				{/each}
			</div>
		</div>
		<div class="column" style="flex: 1;">
			<h1>Stuff</h1>
			<br>
		</div>
	</div>
</div>


<style>
	h1 {
		text-align: center;
	}

	.chat {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
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
		background-color: #eee;
		border-radius: 1em 1em 1em 0;
	}

	.author span {
		font-size: medium;
		background-color: #0074D9;
		color: white;
		border-radius: 1em 1em 0 1em;
		word-break: break-all;
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
		height: 100%
	}
</style>