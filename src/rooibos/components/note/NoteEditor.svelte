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
  import TipTapBubbleMenu from '@tiptap/extension-bubble-menu';
  import BubbleMenu from './BubbleMenu.svelte';
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
  
  // 버블 메뉴 관련
  let bubbleMenuElement;
  
  // 에디터 상태 변경 감지를 위한 변수
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

  // 드롭다운 위치 계산을 위한 변수
  let colorPickerPosition = { x: 0, y: 0 };
  let highlightPickerPosition = { x: 0, y: 0 };
  let alignmentDropdownPosition = { x: 0, y: 0 };

  // 링크 관련 변수
  let showLinkInput = false;
  let linkInputPosition = { x: 0, y: 0 };
  let linkInputValue = '';

  let showColorPicker = false;
  let showHighlightPicker = false;
  let showAlignmentOptions = false;

  // 버블 메뉴 위치 조정 함수
  function adjustBubbleMenuPosition() {
    if (!bubbleMenuElement) return;
    
    const rect = bubbleMenuElement.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    
    if (rect.right > viewportWidth) {
      const overflow = rect.right - viewportWidth;
      bubbleMenuElement.style.transform = `translateX(-${overflow + 10}px)`;
    } else {
      bubbleMenuElement.style.transform = '';
    }
  }

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
    
    setTimeout(adjustBubbleMenuPosition, 0);
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
      })
        .then(res => res.json())
        .then(data => data.translatedText);
      
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

  // 액션 함수들
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
    toggleHighlight();
  }
  
  function toggleHighlight() {
    if (!editor) return;
    
    const isHighlighted = editor.isActive('highlight');
    
    if (isHighlighted) {
      editor.chain().focus().unsetHighlight().run();
    } else {
      editor.chain().focus().setHighlight({ color: '#FFFF00' }).run();
    }
    
    updateEditorState();
  }
  
  function toggleAlignmentOptions(event) {
    event.stopPropagation();
    const buttonRect = event.currentTarget.getBoundingClientRect();
    alignmentDropdownPosition = {
      x: buttonRect.left,
      y: buttonRect.bottom + 10
    };
    
    showAlignmentOptions = !showAlignmentOptions;
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
  
  function setTextAlignLeft() {
    if (!editor) return;
    editor.chain().focus().setTextAlign('left').run();
    checkAlignmentState();
    updateEditorState();
  }
  
  function setTextAlignCenter() {
    if (!editor) return;
    editor.chain().focus().setTextAlign('center').run();
    checkAlignmentState();
    updateEditorState();
  }
  
  function setTextAlignRight() {
    if (!editor) return;
    editor.chain().focus().setTextAlign('right').run();
    checkAlignmentState();
    updateEditorState();
  }
  
  function checkAlignmentState() {
    if (!editor) return;
    
    try {
      const isLeftAligned = editor.isActive({ textAlign: 'left' });
      const isCenterAligned = editor.isActive({ textAlign: 'center' });
      const isRightAligned = editor.isActive({ textAlign: 'right' });
      
      editorState = {
        ...editorState,
        textAlignLeft: isLeftAligned,
        textAlignCenter: isCenterAligned,
        textAlignRight: isRightAligned
      };
      
      console.log('정렬 상태:', { 왼쪽: isLeftAligned, 가운데: isCenterAligned, 오른쪽: isRightAligned });
    } catch (error) {
      console.error('정렬 상태 확인 중 오류:', error);
    }
  }
  
  function removeFormat() {
    if (!editor) return;
    
    editor.chain().focus()
      .unsetAllMarks()
      .clearNodes()
      .setTextAlign('left')
      .run();
    
    editorState = {
      ...editorState,
      bold: false,
      italic: false,
      underline: false,
      strike: false,
      textStyle: false,
      highlight: false,
      link: false,
      textAlignLeft: true,
      textAlignCenter: false,
      textAlignRight: false
    };
    
    checkAlignmentState();
    updateEditorState();
    
    setTimeout(() => {
      if (editor) {
        checkAlignmentState();
        updateEditorState();
      }
    }, 50);
  }
  
  function setLink() {
    if (!editor) return;
    
    const selection = editor.state.selection;
    const hasLink = editor.isActive('link');
    
    if (selection.empty && !hasLink) {
      return;
    }
    
    const bubbleRect = bubbleMenuElement.getBoundingClientRect();
    linkInputPosition = {
      x: bubbleRect.left,
      y: bubbleRect.bottom + 10
    };
    
    const previousUrl = editor.getAttributes('link').href || '';
    linkInputValue = previousUrl;
    
    showLinkInput = true;
    showColorPicker = false;
    showHighlightPicker = false;
    showAlignmentOptions = false;
    
    setTimeout(() => {
      const linkInput = document.getElementById('link-input');
      if (linkInput) linkInput.focus();
    }, 10);
  }
  
  function applyLink() {
    if (!editor) return;
    
    if (linkInputValue === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
    } else {
      editor.chain().focus().extendMarkRange('link').setLink({ href: linkInputValue }).run();
    }
    
    showLinkInput = false;
    updateEditorState();
  }
  
  function handleLinkInputKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      applyLink();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      cancelLinkInput();
    }
  }
  
  function cancelLinkInput() {
    showLinkInput = false;
    linkInputValue = '';
  }
  
  function closeAllDropdowns() {
    showColorPicker = false;
    showHighlightPicker = false;
    showAlignmentOptions = false;
  }
  
  function handleTitleChange(e) {
    pageTitle = e.detail;
    manualTitleEdited = true;
    if (editor) {
      const htmlContent = editor.getHTML();
      updateNote(localStorage.token, noteId, pageTitle, htmlContent);
    }
  }
  
  function openSidebar() {
    showSidebar = true;
  }
  
  function closeSidebar() {
    showSidebar = false;
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
          openOnClick: true,
          HTMLAttributes: {
            class: 'custom-link',
            target: '_blank',
            rel: 'noopener noreferrer'
          },
        }),
        TipTapBubbleMenu.configure({
          element: bubbleMenuElement,
          shouldShow: ({ editor, from, to }) => {
            const isVisible = from !== to && editor.isEditable;
            if (isVisible) {
              setTimeout(adjustBubbleMenuPosition, 0);
            }
            return isVisible;
          },
          tippyOptions: {
            duration: 100,
            placement: 'top-start',
            offset: [0, 25],
            theme: 'bubble-menu-theme',
            onShow: () => {
              setTimeout(adjustBubbleMenuPosition, 0);
            }
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
    
    updateEditorState();
    document.addEventListener('click', closeAllDropdowns);
    window.addEventListener('resize', adjustBubbleMenuPosition);
  });

  onDestroy(() => {
    if (editor) {
      editor.destroy();
    }
    document.removeEventListener('click', closeAllDropdowns);
    window.removeEventListener('resize', adjustBubbleMenuPosition);
  });
</script>

<TopBar {pageTitle} on:titleChange={handleTitleChange} onNewChat={openSidebar} />

<div class="notion-page-container">
  <div class="editor-wrapper" bind:this={editorElement}></div>

  <!-- BubbleMenu 컴포넌트 사용 -->
  <BubbleMenu
    bind:menuElement={bubbleMenuElement}
    {editorState}
    onToggleBold={toggleBold}
    onToggleItalic={toggleItalic}
    onToggleUnderline={toggleUnderline}
    onToggleStrike={toggleStrike}
    onToggleColorPicker={toggleColorPicker}
    onToggleHighlightPicker={toggleHighlightPicker}
    onToggleAlignmentOptions={toggleAlignmentOptions}
    onSetLink={setLink}
    onTranslate={translateSelectedText}
    onRemoveFormat={removeFormat}
  />
</div>

{#if showSidebar}
  <RightSidebar on:close={closeSidebar} />
{/if}

<!-- 포털 컨테이너 -->
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

  {#if showLinkInput}
    <div class="floating-dropdown floating-link-input" style="position: fixed; left: {linkInputPosition.x}px; top: {linkInputPosition.y}px; border: 1px solid #ddd;">
      <div class="link-input-container">
        <div class="link-input-row">
          <input 
            id="link-input"
            type="text" 
            bind:value={linkInputValue} 
            placeholder="URL 입력" 
            on:keydown={handleLinkInputKeydown}
          />
          <button class="link-button" on:click={applyLink}>적용</button>
        </div>
      </div>
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
    position: fixed !important;
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
  
  .floating-link-input {
    width: 300px;
  }
  
  .link-input-container {
    display: flex;
    padding: 4px;
  }
  
  .link-input-row {
    display: flex;
    width: 100%;
    align-items: center;
  }
  
  .link-input-container input {
    flex: 1;
    padding: 6px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    margin-right: 4px;
  }
  
  .link-button {
    padding: 6px 10px;
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    white-space: nowrap;
  }
  
  .link-button:hover {
    background-color: #e5e5e5;
  }
</style>
