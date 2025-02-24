<script>
    import { onMount, onDestroy, tick } from 'svelte';
    import { Editor } from '@tiptap/core';
    import StarterKit from '@tiptap/starter-kit';
    import TopBar from './TopBar.svelte';
    import RightSidebar from './NoteAIChat.svelte';
  
    let editor;
    let editorElement;
    let pageTitle = "새 페이지";
    let showSidebar = false;
  
    // 에디터의 JSON에서 제목(첫 번째 h1)을 추출하는 함수
    function updatePageTitle() {
      const json = editor.getJSON();
      let newTitle = "새 페이지";
      if (json.content && json.content.length > 0) {
        const heading = json.content.find(
          node => node.type === 'heading' && node.attrs && node.attrs.level === 1
        );
        if (heading && heading.content && heading.content.length > 0 && heading.content[0].text) {
          newTitle = heading.content[0].text;
        }
      }
      pageTitle = newTitle;
    }
  
    onMount(() => {
      editor = new Editor({
        element: editorElement,
        extensions: [StarterKit],
        content: `<p class="subtitle"></p>`,
        autofocus: true,
        onUpdate({ editor }) {
          updatePageTitle();
          console.log('변경된 내용:', editor.getJSON());
        }
      });
    });

  
    onDestroy(() => {
      if (editor) {
        editor.destroy();
      }
      editor.commands.focus();
    });
  
    function openSidebar() {
      showSidebar = true;
    }
  
    function closeSidebar() {
      showSidebar = false;
    }
  </script>
  
  <!-- 상단 바 (TopBar) 컴포넌트 -->
  <TopBar {pageTitle} onNewChat={openSidebar} />
  
  <!-- 화면 전체를 감싸는 컨테이너 -->
  <div class="notion-page-container">
    <!-- 에디터가 렌더링 될 영역 -->
    <div class="editor-wrapper" bind:this={editorElement}></div>
  </div>
  
  <!-- 우측 사이드바 (조건부 렌더링) -->
  {#if showSidebar}
    <RightSidebar on:close={closeSidebar} />
  {/if}
  
  <style>
    .notion-page-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 2rem;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
        Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
      color: #2e2e2e;
    }
    .title {
      font-size: 2.5rem;
      font-weight: 700;
      margin: 2rem 0 0.5rem 0;
      outline: none;
      border: none;
      padding: 0;
    }
    .subtitle {
      font-size: 1rem;
      color: #888;
      margin-bottom: 1.5rem;
    }
    .editor-wrapper {
      min-height: 400px;
      outline: none;
      border: none;
      padding: 0;
    }
    .editor-wrapper :focus {
      outline: none;
    }
  </style>
  