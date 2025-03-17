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

	// 기존 update 함수
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

	// 변경 시 자동 저장 이벤트를 발생시키는 함수 (debounce 적용)
	const debouncedAutoSave = debounce(() => {
		updateContent();
		updateTitle();
		dispatch('autosave', { name, content });
	}, 3000);

	// 에디터 변경 시 호출되는 통합 핸들러
	function handleEditorChange() {
		updateContent();
		updateTitle();
		debouncedAutoSave();
	}

	// 주기적으로 자동 저장 실행
	function setupAutoSave() {
		if (autoSaveInterval) clearInterval(autoSaveInterval);
		
		autoSaveInterval = setInterval(() => {
			if (show && noteEditor) {
				updateContent();
				updateTitle();
				dispatch('autosave', { name, content });
			}
		}, 30000); // 30초마다 자동 저장
	}

	$: if (show && noteEditor) {
		// show가 true로 변경될 때 초기값 설정
		name = initialTitle || 'Untitled';
		content = initialContent || '';
		setupAutoSave();
	}

	async function handleSubmit() {
		// 수동 저장 시에는 debounce 취소 후 즉시 처리
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
	}

	onMount(() => {
		if (show) {
			setupAutoSave();
		}
	});

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
		<!-- 수동 저장(X 마크) 버튼: 누르면 자동 저장 취소 후 제출 -->
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
					<!-- NoteEditor의 change와 titleChange 이벤트 모두 handleEditorChange를 호출 -->
					<NoteEditor 
						bind:this={noteEditor}
						on:change={handleEditorChange}
						on:titleChange={handleEditorChange}
						initialTitle={initialTitle}
						initialContent={initialContent}
						selectedFile={selectedFile}
					/>
				{/if}
			</div>
		</div>
	</div>
</Modal>
