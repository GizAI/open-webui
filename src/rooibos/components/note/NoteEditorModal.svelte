<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import NoteEditor from '$rooibos/components/note/NoteEditor.svelte';
	
	export let show = false;
	export let initialTitle: string = '';
	export let initialContent: any = '';
	export let selectedFile: any;

	let name = 'Untitled';
	let content = '';
	let noteEditor: any;

	function updateContent() {
		if (noteEditor && noteEditor.getContent) {
			content = noteEditor.getContent();
		}
	}

	function updateTitle() {
		if (noteEditor && noteEditor.getTitle) {
			name = noteEditor.getTitle();
		}
	}
	

	async function handleSubmit() {
		await updateContent();
		await updateTitle();

		dispatch('submit', {
			name,
			content
		});
		show = false;
		name = '';
		content = '';
	}
</script>

<Modal 
	size="full" 
	containerClassName="" 
	className="h-full bg-white dark:bg-gray-900" 
	bind:show
>
	<div class="absolute top-0 right-0 p-5 z-10">
		<button
			class="self-center dark:text-white"
			type="button"
			on:click={async () => {
				await handleSubmit();
			}}
		>
			<XMark className="size-3.5" />
		</button>
	</div>
	
	<div class="flex flex-col w-full h-full dark:text-gray-200">
		<div class="flex-1 w-full h-full flex justify-center overflow-auto">
			<div class="w-full h-full flex flex-col">
				{#if show}
					<NoteEditor 
						bind:this={noteEditor}
						on:change={updateContent}
						on:titleChange={updateTitle}
						initialTitle={initialTitle}
						initialContent={initialContent}
						selectedFile={selectedFile}
					/>
				{/if}
			</div>
		</div>
	</div>
</Modal> 