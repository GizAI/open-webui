<script lang="ts">
  import { showSidebar } from '$lib/stores';
  import MenuLines from '$lib/components/icons/MenuLines.svelte';
  import { get } from 'svelte/store';

  // 실제 제목 값은 비어있는 상태로 시작
  export let pageTitle = "";
  export let onNewChat = () => {};

  // 처음부터 입력 모드로 시작
  let editing = true;
  let inputValue = "";
  const placeholder = "새 페이지";

  function handleBlur() {
    // 입력값이 없으면 기본 placeholder 적용
    if (!inputValue.trim()) {
      pageTitle = placeholder;
      inputValue = placeholder;
    } else {
      pageTitle = inputValue;
    }
    editing = false;
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      (e.target as HTMLInputElement).blur();
    }
  }
</script>

<!-- 상단바 전체 컨테이너 -->
<div class="top-bar">
  <!-- 왼쪽 영역: 메뉴 버튼과 페이지 제목을 한 줄에 배치 -->
  <div class="left">
    {#if !$showSidebar}
      <button
        id="sidebar-toggle-button"
        class="sidebar-toggle-button"
        on:click={() => showSidebar.set(true)}
        aria-label="Toggle Sidebar"
      >
        <MenuLines />
      </button>
    {/if}
    {#if editing}
      <input
        class="page-title-input"
        bind:value={inputValue}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        placeholder={placeholder}
        autofocus
      />
    {:else}
      <span
        class="page-title"
        on:click={() => {
          editing = true;
          // 제목이 기본 placeholder인 경우 입력값은 빈 문자열로 설정하여 텍스트가 사라지도록 함
          inputValue = pageTitle === placeholder ? "" : pageTitle;
        }}
      >
        {pageTitle === "" ? placeholder : pageTitle}
      </span>
    {/if}
  </div>

  <!-- 오른쪽 영역: 새 채팅 버튼 -->
  <div class="right">
    <button on:click={onNewChat} class="new-chat-btn">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="icon"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
        />
      </svg>
      <span class="btn-text">AI채팅</span>
    </button>
  </div>
</div>

<style>
  .top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #fff;
    padding: 0.5rem 1rem;
  }
  /* 왼쪽 영역: 메뉴 버튼과 페이지 제목을 한 줄에 배치 */
  .left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .page-title {
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
  }
  .sidebar-toggle-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
  }
  .right .new-chat-btn {
    background: none;
    border: none;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .icon {
    height: 1.25rem;
    width: 1.25rem;
    color: #555;
  }
  .btn-text {
    font-size: 0.75rem;
    color: #555;
    margin-top: 0.25rem;
    white-space: nowrap;
  }
  .page-title-input {
    font-size: 1rem;
    font-weight: bold;
    border: none;
    outline: none;
  }
</style>
