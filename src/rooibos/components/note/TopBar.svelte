<!-- TopBar.svelte-->
<script lang="ts">
  import { showSidebar } from '$lib/stores';
  import MenuLines from '$lib/components/icons/MenuLines.svelte';
  import { createEventDispatcher } from 'svelte';
  import { updateFileFilenameById } from '$lib/apis/files';

  const dispatch = createEventDispatcher();
  export let pageTitle = "";
  export let onNewChat = () => {};
  export let fileId = "";
  export let token = "";
  export let originalFilename = "";

  let editing = false;
  let inputValue = "";
  const placeholder = "";
  let displayTitle = "";

  // 파일 확장자 추출 함수
  function getFileExtension(filename: string): string {
    const lastDotIndex = filename.lastIndexOf('.');
    if (lastDotIndex === -1) return '';
    return filename.substring(lastDotIndex);
  }

  // 파일명에서 확장자를 제외한 부분 추출
  function getFilenameWithoutExtension(filename: string): string {
    const lastDotIndex = filename.lastIndexOf('.');
    if (lastDotIndex === -1) return filename;
    return filename.substring(0, lastDotIndex);
  }

  // 페이지 타이틀이 변경될 때 표시용 타이틀 업데이트
  $: {
    if (pageTitle) {
      displayTitle = getFilenameWithoutExtension(pageTitle);
    } else {
      displayTitle = placeholder;
    }
  }

  $: if (!editing) {
    inputValue = displayTitle;
  }

  // 파일 ID가 유효한지 확인하는 함수
  function isValidFileId(id: string): boolean {
    // temp-id는 유효한 파일 ID로 간주하지 않음
    if (id && typeof id === 'string' && id.includes('temp-id')) {
      return false;
    }
    return Boolean(id && typeof id === 'string' && id.trim() !== '');
  }

  async function handleBlur() {
    if (!inputValue.trim()) {
      displayTitle = placeholder;
      inputValue = placeholder;
      pageTitle = originalFilename || placeholder;
    } else {
      displayTitle = inputValue;
      
      // 원본 파일명에서 확장자 추출
      const extension = getFileExtension(originalFilename || "");
      
      // 새 파일명에 확장자 추가 (내부적으로만 사용)
      if (extension) {
        pageTitle = inputValue + extension;
      } else {
        pageTitle = inputValue;
      }
    }
    editing = false;
    
    // 파일 ID가 있을 때만 파일명 업데이트 API 호출
    if (isValidFileId(fileId) && pageTitle !== placeholder && pageTitle !== originalFilename) {
      try {
        await updateFileFilenameById(token, fileId, pageTitle);
      } catch (error) {
        console.error('Failed to update file name:', error);
      }
    }
    
    dispatch('titleChange', pageTitle);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      (e.target as HTMLInputElement).blur();
    }
  }
</script>

<div class="top-bar bg-white dark:bg-gray-900">
  <div class="left">
    {#if editing}
      <input
        class="page-title-input bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-200"
        bind:value={inputValue}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        placeholder={placeholder}
        autofocus
      />
    {:else}
      <button
        type="button"
        class="page-title text-gray-900 dark:text-gray-200 bg-transparent border-none p-0 cursor-pointer"
        on:click={() => {
          editing = true;
          inputValue = displayTitle === placeholder ? "" : displayTitle;
        }}
        on:keydown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            editing = true;
            inputValue = displayTitle === placeholder ? "" : displayTitle;
          }
        }}
      >
        {displayTitle === "" ? placeholder : displayTitle}
      </button>
    {/if}
  </div>
</div>

<style>
  .top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
  }
  
  .left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .page-title {
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    color: #333;
  }
  
  :global(.dark) .page-title {
    color: #e5e7eb;
  }
  
  .sidebar-toggle-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
    color: #555;
  }
  
  :global(.dark) .sidebar-toggle-button {
    color: #e5e7eb;
  }
  
  .page-title-input {
    font-size: 1rem;
    font-weight: bold;
    border: none;
    outline: none;
  }
  
  :global(.dark) .page-title-input {
    color: #e5e7eb;
  }
</style>
