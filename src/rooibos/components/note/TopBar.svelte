<!-- TopBar.svelte-->
<script lang="ts">
  import { showSidebar } from '$lib/stores';
  import MenuLines from '$lib/components/icons/MenuLines.svelte';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();
  export let pageTitle = "";
  export let onNewChat = () => {};

  let editing = false;
  let inputValue = "";
  const placeholder = "새 페이지";

  $: if (!editing) {
    inputValue = pageTitle;
  }

  function handleBlur() {
    if (!inputValue.trim()) {
      pageTitle = placeholder;
      inputValue = placeholder;
    } else {
      pageTitle = inputValue;
    }
    editing = false;
    dispatch('titleChange', pageTitle);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      (e.target as HTMLInputElement).blur();
    }
  }
</script>

<div class="top-bar">
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
          inputValue = pageTitle === placeholder ? "" : pageTitle;
        }}
      >
        {pageTitle === "" ? placeholder : pageTitle}
      </span>
    {/if}
  </div>

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
