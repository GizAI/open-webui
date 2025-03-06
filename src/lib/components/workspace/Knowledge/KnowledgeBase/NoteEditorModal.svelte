<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import NoteEditor from '$rooibos/components/note/NoteEditor.svelte';
	
	export let show = false;

	let name = 'Untitled';
	let content = '';
	let noteEditor: any;

	// 에디터 내용이 변경될 때마다 content 변수 업데이트
	function updateContent() {
		if (noteEditor && noteEditor.getContent) {
			content = noteEditor.getContent();
		}
	}

	// 에디터 제목이 변경될 때마다 name 변수 업데이트
	function updateTitle() {
		if (noteEditor && noteEditor.getTitle) {
			name = noteEditor.getTitle();
		}
	}

	async function handleSubmit() {
		// 제출 전에 최신 내용과 제목 가져오기
		await updateContent();
		await updateTitle();

		if (name.trim() === '' || content.trim() === '') {
			toast.error($i18n.t('Please fill in all fields.'));
			name = name.trim();
			content = content.trim();
			return;
		}

		dispatch('submit', {
			name,
			content
		});
		show = false;
		name = '';
		content = '';
	}
</script>

<Modal size="full" containerClassName="" className="h-full bg-white dark:bg-gray-900" bind:show>
	<div class="absolute top-0 right-0 p-5 z-10">
		<button
			class="self-center dark:text-white"
			type="button"
			on:click={() => {
				show = false;
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
					/>
				{/if}
			</div>
		</div>

		<div class="flex flex-row items-center justify-end text-sm font-medium shrink-0 mt-1 p-4 gap-1.5">
			<button
				class="px-3.5 py-2 bg-black text-white dark:bg-white dark:text-black transition rounded-full"
				on:click={handleSubmit}
			>
				{$i18n.t('Save')}
			</button>
		</div>
	</div>
</Modal> 