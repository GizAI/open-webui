<!-- NoteEditorModal.svelte -->
<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, createEventDispatcher, onDestroy, onMount } from 'svelte';
	import { debounce } from 'lodash-es';
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
	let autoSaveInterval: any;
	
	let previousContent = '';
	let previousTitle = '';

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

	function hasContentChanged() {
		const currentContent = noteEditor?.getContent() || '';
		const currentTitle = noteEditor?.getTitle() || '';
		
		const contentChanged = currentContent !== previousContent;
		const titleChanged = currentTitle !== previousTitle;
		
		if (contentChanged) {
			previousContent = currentContent;
		}
		
		if (titleChanged) {
			previousTitle = currentTitle;
		}
		
		return contentChanged || titleChanged;
	}

	const debouncedAutoSave = debounce(() => {
		if (hasContentChanged()) {
			updateContent();
			updateTitle();
			dispatch('autosave', { name, content });
		}
	}, 3000);

	function handleEditorChange() {
		updateContent();
		updateTitle();
		debouncedAutoSave();
	}
	

	$: if (show && noteEditor) {
		name = initialTitle || 'Untitled';
		content = initialContent || '';
		previousContent = content;
		previousTitle = name;
	}

	async function handleSubmit() {
		debouncedAutoSave.cancel();
		updateContent();
		updateTitle();
		
		dispatch('submit', {
			name,
			content
		});
		
		show = false;
		name = '';
		content = '';
		previousContent = '';
		previousTitle = '';
	}

	function setupAutoSaveInterval() {
		if (autoSaveInterval) {
			clearInterval(autoSaveInterval);
		}
		
		autoSaveInterval = setInterval(() => {
			if (show && noteEditor && hasContentChanged()) {
				updateContent();
				updateTitle();
				dispatch('autosave', { name, content });
			}
		}, 30000);
	}

	onMount(() => {
		setupAutoSaveInterval();
	});

	$: if (show) {
		setupAutoSaveInterval();
	}

	onDestroy(() => {
		debouncedAutoSave.cancel();
		if (autoSaveInterval) clearInterval(autoSaveInterval);
	});
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
						on:change={(e) => {
							handleEditorChange();
						}}
						on:titleChange={(e) => {
							handleEditorChange();
						}}
						initialTitle={initialTitle}
						initialContent={initialContent}
						selectedFile={selectedFile}
					/>
				{/if}
			</div>
		</div>
	</div>
</Modal>
