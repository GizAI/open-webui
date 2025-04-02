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
	import TopBar from '$rooibos/components/note/TopBar.svelte';
	
	export let show = false;
	export let initialTitle: string = '';
	export let initialContent: any = '';
	export let selectedFile: any;

	let name = 'Untitled';
	let content = '';
	let noteEditor: any;
	let pageTitle = initialTitle || '새노트';
	
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
	
	function getFileId(): string {
		if (!selectedFile) return "";
		return selectedFile.id || "";
	}

	function getOriginalFilename(): string {
		if (!selectedFile) return "";
		return selectedFile.filename || selectedFile.name || "";
	}

	function handleTitleChange(e: CustomEvent<string>): void {
		let newTitle = e.detail;
		
		// 이름을 직접 업데이트하여 파일명에 반영
		let cleanedTitle = newTitle;
		while(cleanedTitle.toLowerCase().endsWith('.txt')) {
			cleanedTitle = cleanedTitle.substring(0, cleanedTitle.length - 4);
		}
		
		// 내부 이름 변수 업데이트
		name = cleanedTitle;
		pageTitle = cleanedTitle;
		
		if (selectedFile) {
			// 확장자 관리 로직
			if (selectedFile.name) {
				// .txt 확장자 한 번만 추가
				selectedFile.name = cleanedTitle + '.txt';
			}
			
			if (selectedFile.filename) {
				const extension = selectedFile.filename.substring(selectedFile.filename.lastIndexOf('.'));
				if (extension.toLowerCase() === '.txt') {
					selectedFile.filename = cleanedTitle + '.txt';
				} else {
					selectedFile.filename = cleanedTitle + extension;
				}
			}
			
			if (selectedFile.meta && selectedFile.meta.name) {
				// 메타데이터 이름에도 .txt 확장자 한 번만 추가
				selectedFile.meta.name = cleanedTitle + '.txt';
			}
		}
		
		// 자동 저장 트리거
		updateContent();
		updateTitle();
		
		// 바로 autosave 이벤트 발생시켜 변경사항을 즉시 저장
		dispatch('autosave', { name: cleanedTitle, content });
	}

	function openSidebar() {
		// 필요한 경우 사이드바 열기 로직 구현
	}

	$: if (show && noteEditor) {
		name = initialTitle || 'Untitled';
		content = initialContent || '';
		pageTitle = initialTitle || '새노트';
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

	onDestroy(() => {
		debouncedAutoSave.cancel();
	});
</script>

<Modal 
	size="full" 
	containerClassName="" 
	className="h-full bg-white dark:bg-gray-900 overflow-hidden" 
	bind:show
>
	<div class="absolute top-0 left-0 right-0 flex justify-between items-center w-full pr-5 pl-5 py-2 z-20 bg-white dark:bg-gray-900">
		<div class="flex-1">
			<TopBar 
				pageTitle={pageTitle} 
				on:titleChange={handleTitleChange} 
				onNewChat={openSidebar} 
				fileId={getFileId()} 
				token={localStorage.getItem('token') || ""}
				originalFilename={getOriginalFilename()}
			/>
		</div>
		<button
			class="self-center dark:text-white ml-2"
			type="button"
			on:click={async () => {
				await handleSubmit();
			}}
		>
			<XMark className="size-3.5" />
		</button>
	</div>
	
	<div class="flex flex-col w-full h-full dark:text-gray-200 pt-12 overflow-auto">
		<div class="flex-1 w-full flex justify-center">
			<div class="w-full flex flex-col">
				{#if show}
					<NoteEditor 
						bind:this={noteEditor}
						on:change={(e) => {
							handleEditorChange();
						}}
						on:titleChange={(e) => {
							handleTitleChange(e);
						}}
						initialTitle={pageTitle}
						initialContent={initialContent}
						selectedFile={selectedFile}
					/>
				{/if}
			</div>
		</div>
	</div>
</Modal>

<style>
/* TopBar 버튼이 클릭 가능하도록 스타일 추가 */
:global(.top-bar) {
	position: relative;
	z-index: 30;
}

:global(.page-title), :global(.page-title-input) {
	position: relative;
	z-index: 40;
	pointer-events: auto;
}
</style>
