<!-- NoteEditor.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import StarterKit from '@tiptap/starter-kit';
  import Underline from '@tiptap/extension-underline';
  import TextStyle from '@tiptap/extension-text-style';
  import Color from '@tiptap/extension-color';
  import Highlight from '@tiptap/extension-highlight';
  import TextAlign from '@tiptap/extension-text-align';
  import Link from '@tiptap/extension-link';
  import BubbleMenu from '@tiptap/extension-bubble-menu';
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
  let bubbleMenuElement;
  
  let showColorPicker = false;
  let showHighlightPicker = false;
  let showAlignmentOptions = false;
  
  // 에디터 상태 변경 감지를 위한 변수 추가
  let editorState = {
    bold: false,
    italic: false,
    underline: false,
    strike: false,
    textStyle: false,
    highlight: false,
    link: false,
    textAlignLeft: false,
    textAlignCenter: false,
    textAlignRight: false
  };

  const { id: noteId } = get(page).params;  

  // 드롭다운 위치 계산을 위한 변수 추가
  let colorPickerPosition = { x: 0, y: 0 };
  let highlightPickerPosition = { x: 0, y: 0 };
  let alignmentDropdownPosition = { x: 0, y: 0 };
  
  // 에디터 상태 업데이트 함수
  function updateEditorState() {
    if (!editor) return;
    
    editorState = {
      bold: editor.isActive('bold'),
      italic: editor.isActive('italic'),
      underline: editor.isActive('underline'),
      strike: editor.isActive('strike'),
      textStyle: editor.isActive('textStyle'),
      highlight: editor.isActive('highlight'),
      link: editor.isActive('link'),
      textAlignLeft: editor.isActive({ textAlign: 'left' }),
      textAlignCenter: editor.isActive({ textAlign: 'center' }),
      textAlignRight: editor.isActive({ textAlign: 'right' })
    };
  }

  async function translateSelectedText() {
    if (!editor) return;
    
    const { from, to } = editor.state.selection;
    if (from === to) return;
    
    const selectedText = editor.state.doc.textBetween(from, to);
    
    try {
      const translatedText = await fetch('https://api.example.com/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: selectedText, target: 'en' })
      }).then(res => res.json()).then(data => data.translatedText);
      
      editor.chain().focus().deleteSelection().insertContent(translatedText).run();
      updateEditorState();
    } catch (error) {
      console.error('번역 중 오류 발생:', error);
    }
  }

  function updateNoteContent() {
    const htmlContent = editor.getHTML();
    
    let newTitle = pageTitle;
    if (!manualTitleEdited && editor.getJSON().content && editor.getJSON().content.length > 0) {
      const heading = editor.getJSON().content.find(
        node => node.type === 'heading' && node.attrs && node.attrs.level === 1
      );
      if (heading && heading.content && heading.content.length > 0 && heading.content[0].text) {
        newTitle = heading.content[0].text;
      }
    }
    pageTitle = newTitle;
    updateNote(localStorage.token, noteId, newTitle, htmlContent);
  }

  onMount(async () => {
    note = await getNote(noteId);

    if (note && note.title) {
      pageTitle = note.title;
    }

    let contentToLoad = `<p class="subtitle"></p>`;
    if (note && note.content) {
      if (typeof note.content === 'string') {
        contentToLoad = note.content;
      } else {
        try {
          editor = new Editor({
            extensions: [
              StarterKit,
              Underline,
              TextStyle,
              Color,
              Highlight,
              TextAlign.configure({
                types: ['heading', 'paragraph'],
              }),
              Link,
            ],
            content: note.content
          });
          contentToLoad = editor.getHTML();
          editor.destroy();
        } catch(e) {
          contentToLoad = `<p class="subtitle"></p>`;
        }
      }
    }

    editor = new Editor({
      element: editorElement,
      extensions: [
        StarterKit,
        Underline,
        TextStyle,
        Color,
        Highlight,
        TextAlign.configure({
          types: ['heading', 'paragraph'],
        }),
        Link.configure({
          openOnClick: false,
          HTMLAttributes: {
            class: 'custom-link',
          },
        }),
        BubbleMenu.configure({
          element: bubbleMenuElement,
          shouldShow: ({ editor, view, state, oldState, from, to }) => {
            return from !== to && editor.isEditable;
          },
          tippyOptions: {
            duration: 100,
            placement: 'top-start',
            offset: [0, 25],
            theme: 'bubble-menu-theme'
          }
        }),
      ],
      content: contentToLoad,
      autofocus: true,
      onUpdate({ editor }) {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
          updateNoteContent();
          console.log('변경된 HTML 내용:', editor.getHTML());
        }, 1000); 
      },
      onSelectionUpdate({ editor }) {
        updateEditorState();
      }
    });
    
    // 초기 상태 업데이트
    updateEditorState();

    // 문서 클릭 이벤트 리스너 추가
    document.addEventListener('click', closeAllDropdowns);
  });

  function handleTitleChange(e) {
    pageTitle = e.detail;
    manualTitleEdited = true;
    if (editor) {
      const htmlContent = editor.getHTML();
      updateNote(localStorage.token, noteId, pageTitle, htmlContent);
    }
  }

  function setLink() {
    if (!editor) return;
    
    const previousUrl = editor.getAttributes('link').href;
    const url = window.prompt('URL', previousUrl);

    if (url === null) {
      return;
    }

    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
      updateEditorState();
      return;
    }

    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
    updateEditorState();
  }

  function removeLink() {
    if (!editor) return;
    editor.chain().focus().extendMarkRange('link').unsetLink().run();
    updateEditorState();
  }

  function removeFormat() {
    if (!editor) return;
    editor.chain().focus().unsetAllMarks().run();
    updateEditorState();
  }

  onDestroy(() => {
    if (editor) {
      editor.destroy();
    }

    // 문서 클릭 이벤트 리스너 제거
    document.removeEventListener('click', closeAllDropdowns);
  });

  function openSidebar() {
    showSidebar = true;
  }

  function closeSidebar() {
    showSidebar = false;
  }

  // 토글 함수 수정
  function toggleColorPicker(event) {
    event.stopPropagation();
    
    const buttonRect = event.currentTarget.getBoundingClientRect();
    colorPickerPosition = {
      x: buttonRect.left,
      y: buttonRect.bottom + 10
    };
    
    showColorPicker = !showColorPicker;
    showHighlightPicker = false;
    showAlignmentOptions = false;
  }
  
  function toggleHighlightPicker(event) {
    event.stopPropagation();
    
    const buttonRect = event.currentTarget.getBoundingClientRect();
    highlightPickerPosition = {
      x: buttonRect.left,
      y: buttonRect.bottom + 10
    };
    
    showHighlightPicker = !showHighlightPicker;
    showColorPicker = false;
    showAlignmentOptions = false;
  }
  
  function toggleAlignmentOptions(event) {
    event.stopPropagation();
    
    const buttonRect = event.currentTarget.getBoundingClientRect();
    // 위치 계산 방식 변경 - 버튼 아래에 표시
    alignmentDropdownPosition = {
      x: buttonRect.left,
      y: buttonRect.bottom + 10 // 버튼 아래에 10px 간격으로 표시
    };
    
    showAlignmentOptions = !showAlignmentOptions;
    console.log('정렬 옵션 토글:', showAlignmentOptions, alignmentDropdownPosition);
    
    // 다른 드롭다운 닫기
    showColorPicker = false;
    showHighlightPicker = false;
  }
  
  function setColor(color) {
    if (!editor) return;
    editor.chain().focus().setColor(color).run();
    showColorPicker = false;
    updateEditorState();
  }

  function setHighlight(color) {
    if (!editor) return;
    editor.chain().focus().toggleHighlight({ color }).run();
    showHighlightPicker = false;
    updateEditorState();
  }
  
  // 버튼 클릭 핸들러에 상태 업데이트 추가
  function toggleBold() {
    if (!editor) return;
    editor.chain().focus().toggleBold().run();
    updateEditorState();
  }
  
  function toggleItalic() {
    if (!editor) return;
    editor.chain().focus().toggleItalic().run();
    updateEditorState();
  }
  
  function toggleUnderline() {
    if (!editor) return;
    editor.chain().focus().toggleUnderline().run();
    updateEditorState();
  }
  
  function toggleStrike() {
    if (!editor) return;
    editor.chain().focus().toggleStrike().run();
    updateEditorState();
  }
  
  function setTextAlignLeft() {
    if (!editor) return;
    editor.chain().focus().setTextAlign('left').run();
    updateEditorState();
  }
  
  function setTextAlignCenter() {
    if (!editor) return;
    editor.chain().focus().setTextAlign('center').run();
    updateEditorState();
  }
  
  function setTextAlignRight() {
    if (!editor) return;
    editor.chain().focus().setTextAlign('right').run();
    updateEditorState();
  }

  // 문서 클릭 시 모든 드롭다운 닫기
  function closeAllDropdowns() {
    showColorPicker = false;
    showHighlightPicker = false;
    showAlignmentOptions = false;
  }
</script>

<TopBar {pageTitle} on:titleChange={handleTitleChange} onNewChat={openSidebar} />

<div class="notion-page-container">
  <div class="editor-wrapper" bind:this={editorElement}></div>
  
  <div class="bubble-menu" bind:this={bubbleMenuElement} style="visibility: hidden; position: absolute; display: inline-flex; align-items: stretch; background: white; overflow: hidden; font-size: 14px; line-height: 1.2; border-radius: 8px; box-shadow: rgba(0, 0, 0, 0.1) 0px 14px 28px -6px, rgba(0, 0, 0, 0.06) 0px 2px 4px -1px, rgba(84, 72, 49, 0.08) 0px 0px 0px 1px; pointer-events: auto; padding: 4px; flex-wrap: nowrap; white-space: nowrap;">
    <button
      class="bubble-menu-button"
      on:click={toggleBold}
      class:active={editorState.bold}
      title="굵게"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
          <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
        </svg>
      </span>
    </button>
    <button
      class="bubble-menu-button"
      on:click={toggleItalic}
      class:active={editorState.italic}
      title="기울임"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="4" x2="10" y2="4"></line>
          <line x1="14" y1="20" x2="5" y2="20"></line>
          <line x1="15" y1="4" x2="9" y2="20"></line>
        </svg>
      </span>
    </button>
    <button
      class="bubble-menu-button"
      on:click={toggleUnderline}
      class:active={editorState.underline}
      title="밑줄"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path>
          <line x1="4" y1="21" x2="20" y2="21"></line>
        </svg>
      </span>
    </button>
    <button
      class="bubble-menu-button"
      on:click={toggleStrike}
      class:active={editorState.strike}
      title="취소선"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"></line>
          <path d="M16 6C16 6 16.5 8 13 10C11 11.5 10 12 10 14C10 16 12 18 16 18"></path>
        </svg>
      </span>
    </button>

    <button
      class="bubble-menu-button"
      on:click={toggleColorPicker}
      class:active={editorState.textStyle}
      title="텍스트 색상"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 19.5H4.5c-1.5 0-3-1.5-3-3 0-1.5 1.5-3 3-3h3v-3h3v3h3c1.5 0 3 1.5 3 3 0 1.5-1.5 3-3 3H12z"/>
          <path d="M16.5 4.5h3v3"/>
          <path d="M19.5 4.5l-6 6"/>
        </svg>
      </span>
    </button>

    <button
      class="bubble-menu-button"
      on:click={toggleHighlightPicker}
      class:active={editorState.highlight}
      title="하이라이트"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2l.642.642L17.5 7.5l-4.5 4.5 5.5 5.5-5.642 5.642L7.5 17.5l4.5-4.5-5.5-5.5L12 2z"/>
        </svg>
      </span>
    </button>

    <button
      class="bubble-menu-button"
      on:click={toggleAlignmentOptions}
      class:active={editorState.textAlignLeft || editorState.textAlignCenter || editorState.textAlignRight}
      title="텍스트 정렬"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </span>
    </button>

    <button
      class="bubble-menu-button"
      on:click={setLink}
      class:active={editorState.link}
      title="링크 추가"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
        </svg>
      </span>
    </button>
    
    <button
      class="bubble-menu-button"
      on:click={removeLink}
      class:active={editorState.link}
      title="링크 제거"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
          <line x1="12" y1="2" x2="12" y2="12"></line>
        </svg>
      </span>
    </button>

    <button
      class="bubble-menu-button"
      on:click={translateSelectedText}
      title="번역"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 8l6 6"></path>
          <path d="M4 14h7"></path>
          <path d="M2 5h12"></path>
          <path d="M7 2v3"></path>
          <path d="M22 22l-5-10-5 10"></path>
          <path d="M14 18h6"></path>
        </svg>
      </span>
    </button>

    <button
      class="bubble-menu-button"
      on:click={removeFormat}
      title="서식 제거"
    >
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="4" x2="20" y2="20"></line>
          <line x1="20" y1="4" x2="4" y2="20"></line>
        </svg>
      </span>
    </button>
  </div>
</div>

{#if showSidebar}
  <RightSidebar on:close={closeSidebar} />
{/if}

<!-- svelte:body 태그 제거하고 포털 컴포넌트 사용 -->
<div class="portal-container">
  {#if showColorPicker}
    <div class="floating-dropdown floating-color-picker" style="position: fixed; left: {colorPickerPosition.x}px; top: {colorPickerPosition.y}px; border: 1px solid #ddd;">
      <button class="color-option" style="background-color: #000000;" on:click={() => setColor('#000000')}></button>
      <button class="color-option" style="background-color: #FF0000;" on:click={() => setColor('#FF0000')}></button>
      <button class="color-option" style="background-color: #00FF00;" on:click={() => setColor('#00FF00')}></button>
      <button class="color-option" style="background-color: #0000FF;" on:click={() => setColor('#0000FF')}></button>
      <button class="color-option" style="background-color: #FFFF00;" on:click={() => setColor('#FFFF00')}></button>
      <button class="color-option" style="background-color: #FF00FF;" on:click={() => setColor('#FF00FF')}></button>
      <button class="color-option" style="background-color: #00FFFF;" on:click={() => setColor('#00FFFF')}></button>
    </div>
  {/if}
  
  {#if showHighlightPicker}
    <div class="floating-dropdown floating-color-picker" style="position: fixed; left: {highlightPickerPosition.x}px; top: {highlightPickerPosition.y}px; border: 1px solid #ddd;">
      <button class="color-option" style="background-color: #FFFF00;" on:click={() => setHighlight('#FFFF00')}></button>
      <button class="color-option" style="background-color: #FFA500;" on:click={() => setHighlight('#FFA500')}></button>
      <button class="color-option" style="background-color: #FF69B4;" on:click={() => setHighlight('#FF69B4')}></button>
      <button class="color-option" style="background-color: #7FFFD4;" on:click={() => setHighlight('#7FFFD4')}></button>
      <button class="color-option" style="background-color: #90EE90;" on:click={() => setHighlight('#90EE90')}></button>
    </div>
  {/if}
  
  {#if showAlignmentOptions}
    <div class="floating-dropdown floating-alignment-dropdown" style="position: fixed; left: {alignmentDropdownPosition.x}px; top: {alignmentDropdownPosition.y}px; border: 1px solid #ddd;">
      <button
        class="alignment-option"
        on:click={setTextAlignLeft}
        class:active={editorState.textAlignLeft}
        title="왼쪽 정렬"
      >
        <span class="icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="12" x2="15" y2="12"></line>
            <line x1="3" y1="18" x2="18" y2="18"></line>
          </svg>
        </span>
      </button>
      <button
        class="alignment-option"
        on:click={setTextAlignCenter}
        class:active={editorState.textAlignCenter}
        title="가운데 정렬"
      >
        <span class="icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="6" y1="12" x2="18" y2="12"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </span>
      </button>
      <button
        class="alignment-option"
        on:click={setTextAlignRight}
        class:active={editorState.textAlignRight}
        title="오른쪽 정렬"
      >
        <span class="icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="9" y1="12" x2="21" y2="12"></line>
            <line x1="6" y1="18" x2="21" y2="18"></line>
          </svg>
        </span>
      </button>
    </div>
  {/if}
</div>

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
  
  .bubble-menu-button {
    background: none;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    color: #333;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    margin: 0;
    transition: background-color 0.2s ease;
  }
  
  .bubble-menu-button:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  .bubble-menu-button.active {
    background-color: rgba(0, 0, 0, 0.1);
    color: #000;
  }
  
  .bubble-menu-button:not(.active) {
    background-color: transparent;
  }
  
  .icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .icon svg {
    width: 14px;
    height: 14px;
  }
  
  .color-picker-container {
    position: relative;
    z-index: 50;
  }
  
  .color-picker {
    position: absolute;
    top: 100%;
    left: 0;
    display: flex;
    flex-wrap: wrap;
    background: white;
    border-radius: 4px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    padding: 4px;
    z-index: 10;
    width: 120px;
  }
  
  .color-option {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 1px solid #ddd;
    margin: 2px;
    cursor: pointer;
  }
  
  .color-option:hover {
    transform: scale(1.1);
  }
  
  :global(.tippy-box[data-theme~='bubble-menu-theme']) {
    background-color: transparent;
    box-shadow: none;
    transform: translateY(-15px);
  }
  
  :global(.tippy-box[data-theme~='bubble-menu-theme'] .tippy-content) {
    padding: 0;
  }
  
  :global(.tippy-box[data-theme~='bubble-menu-theme'] .tippy-arrow) {
    display: none;
  }
  
  :global(.custom-link) {
    color: #0366d6;
    text-decoration: underline;
    cursor: pointer;
  }
  
  :global(.custom-link:hover) {
    text-decoration: none;
  }
  
  .bubble-menu {
    overflow-x: auto;
    max-width: 90vw;
    scrollbar-width: thin;
  }
  
  .bubble-menu::-webkit-scrollbar {
    height: 4px;
  }
  
  .bubble-menu::-webkit-scrollbar-thumb {
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
  }
  
  .floating-dropdown {
    position: fixed !important; /* absolute에서 fixed로 다시 변경 */
    display: flex;
    background: white;
    border-radius: 4px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    padding: 4px;
    z-index: 9999 !important;
    pointer-events: auto;
  }
  
  .floating-color-picker {
    flex-wrap: wrap;
    width: 120px;
  }
  
  .floating-alignment-dropdown {
    flex-direction: column;
    width: 40px;
  }
  
  .portal-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 0;
    overflow: visible;
    pointer-events: none;
    z-index: 9999;
  }
  
  .floating-dropdown {
    pointer-events: auto;
    /* 다른 스타일... */
  }
</style>
