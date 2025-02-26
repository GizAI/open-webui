<!-- NoteEditor.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import StarterKit from '@tiptap/starter-kit';
  import Underline from '@tiptap/extension-underline';
  import TextStyle from '@tiptap/extension-text-style';
  import Color from '@tiptap/extension-color';
  import TextAlign from '@tiptap/extension-text-align';
  import TopBar from './TopBar.svelte';
  import RightSidebar from './NoteAIChat.svelte';
  import { getNote, updateNote } from '../apis/note';
  import { get } from 'svelte/store';
  import { page } from '$app/stores';

  let editor;
  let editorElement;
  let pageTitle = "새 페이지";
  let showSidebar = false;
  let note = {};
  let manualTitleEdited = false;
  let saveTimeout;

  const { id: noteId } = get(page).params;  

  function updateNoteContent() {
    const jsonContent = editor.getJSON();
    
    let newTitle = pageTitle;
    if (!manualTitleEdited && jsonContent.content && jsonContent.content.length > 0) {
      const heading = jsonContent.content.find(
        node => node.type === 'heading' && node.attrs && node.attrs.level === 1
      );
      if (heading && heading.content && heading.content.length > 0 && heading.content[0].text) {
        newTitle = heading.content[0].text;
      }
    }
    pageTitle = newTitle;
    updateNote(localStorage.token, noteId, newTitle, jsonContent);
  }

  onMount(async () => {
    note = await getNote(noteId);

    if (note && note.title) {
      pageTitle = note.title;
    }

    let contentToLoad = `<p class="subtitle"></p>`;
    if (note && note.content) {
      if (typeof note.content === 'string') {
        try {
          contentToLoad = JSON.parse(note.content);
        } catch(e) {
          contentToLoad = note.content;
        }
      } else {
        contentToLoad = note.content;
      }
    }

    editor = new Editor({
      element: editorElement,
      extensions: [
        StarterKit,
        Underline,
        TextStyle,
        Color,
        TextAlign.configure({
          types: ['heading', 'paragraph'],
        }),
      ],
      content: contentToLoad,
      autofocus: true,
      onUpdate({ editor }) {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
          updateNoteContent();
          console.log('변경된 JSON 내용:', editor.getJSON());
        }, 1000); 
      }
    });
  });

  function handleTitleChange(e) {
    pageTitle = e.detail;
    manualTitleEdited = true;
    if (editor) {
      const jsonContent = editor.getJSON();
      updateNote(localStorage.token, noteId, pageTitle, jsonContent);
    }
  }

  onDestroy(() => {
    if (editor) {
      editor.destroy();
    }
  });

  function openSidebar() {
    showSidebar = true;
  }

  function closeSidebar() {
    showSidebar = false;
  }
</script>

<TopBar {pageTitle} on:titleChange={handleTitleChange} onNewChat={openSidebar} />

<div class="notion-page-container">
  <div class="editor-wrapper" bind:this={editorElement}></div>
</div>

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
