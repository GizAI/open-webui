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
      // 입력값에서 확장자 제거 (깨끗한 이름만 가져오기)
      let cleanedInput = inputValue;
      while(cleanedInput.toLowerCase().endsWith('.txt')) {
        cleanedInput = cleanedInput.substring(0, cleanedInput.length - 4);
      }
      
      // 화면에 표시되는 타이틀은 확장자 없는 깔끔한 이름
      displayTitle = cleanedInput;
      
      // 실제 파일명에는 확장자 추가
      const isTxtFile = originalFilename.toLowerCase().endsWith('.txt');
      
      // txt 파일인 경우 항상 .txt 확장자 한 번만 추가
      if (isTxtFile) {
        pageTitle = cleanedInput + '.txt';
      } else {
        // 다른 파일 타입의 경우 원래 확장자 유지
        const extension = getFileExtension(originalFilename || "");
        if (extension) {
          pageTitle = cleanedInput + extension;
        } else {
          pageTitle = cleanedInput;
        }
      }
    }
    editing = false;
    
    // 파일 ID가 있을 때만 파일명 업데이트 API 호출
    if (isValidFileId(fileId) && pageTitle !== placeholder && pageTitle !== originalFilename) {
      try {
        // 확장자가 포함된 전체 파일명으로 API 호출
        console.log('파일명 업데이트:', pageTitle);
        await updateFileFilenameById(token, fileId, pageTitle);
      } catch (error) {
        console.error('Failed to update file name:', error);
      }
    }
    
    // 타이틀 변경 이벤트 발생 (확장자 포함된 전체 이름 전달)
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
