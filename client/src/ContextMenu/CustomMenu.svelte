<script> // https://svelte.dev/repl/3a33725c3adb4f57b46b597f9dade0c1?version=3.25.0
	import Menu from './Menu.svelte';
	import MenuOption from './MenuOption.svelte';
	import MenuDivider from './MenuDivider.svelte';
	import { createEventDispatcher } from 'svelte'
	import IconSave from '../Icons/IconSave.svelte';
	import TrashCan from '../Icons/TrashCan.svelte'
	const dispatch = createEventDispatcher();
	
	let pos = { x: 0, y: 0 };
	let showMenu = false;

	export let hovered_component; // either phrases or saved phrases
	export let hovered_phrase; // the specific json data

	let locked_component; // because the hovered info will change as soon as they leave the hovered phrases
	let locked_phrase;
	
	async function onRightClick(e) {
		locked_component = hovered_component;
		locked_phrase = hovered_phrase;

		if (showMenu) {
			showMenu = false;
			await new Promise(res => setTimeout(res, 100));
		}
		
		pos = { x: e.clientX, y: e.clientY };
		showMenu = true;
	}
	
	function closeMenu() {
		showMenu = false;
	}
</script>

{#if showMenu}
{#if locked_component == "phrases"}
	<Menu {...pos} on:click={closeMenu} on:clickoutside={closeMenu}>
		<MenuOption on:click={dispatch('save-phrase', locked_phrase)}>
			<IconSave />
			<span>Save Phrase</span>
		</MenuOption>
		<MenuDivider />
		<MenuOption on:click={dispatch('delete-phrase', locked_phrase)}>
			<TrashCan />
			<span>Delete</span>
		</MenuOption>
	</Menu>
{:else if locked_component == "saved_phrases"}
	<Menu {...pos} on:click={closeMenu} on:clickoutside={closeMenu}>
		<MenuOption on:click={dispatch('delete-saved-phrase', locked_phrase)}>
			<TrashCan />
			<span>Delete</span>
		</MenuOption>
	</Menu>
{/if}
{/if}

<svelte:body on:contextmenu|preventDefault={onRightClick} />