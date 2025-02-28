<!-- NoteEditor.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import Collaboration from '@tiptap/extension-collaboration';
  import CollaborationCursor from '@tiptap/extension-collaboration-cursor';
  import { HocuspocusProvider } from '@hocuspocus/provider';
  import * as Y from 'yjs';
  import BubbleMenu from './BubbleMenu.svelte';
  import TopBar from './TopBar.svelte';
  import RightSidebar from './NoteAIChat.svelte';
  import CollaboratorsList from './CollaboratorsList.svelte';
  import { getNote, renameNote } from '../apis/note';
  import { get } from 'svelte/store';
  import { page } from '$app/stores';
  import { getExtensions } from './tiptapExtension';
  import { user } from '$lib/stores';

  let editor;
  let editorElement;
  let pageTitle = "새 페이지";
  let showSidebar = false;
  let note = {};
  let manualTitleEdited = false;
  let saveTimeout;
  let bubbleMenuElement;
  
  // 협업 관련 변수
  let provider;
  let activeUsers = [];
  
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

  // 드롭다운 위치 계산 변수들
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
      renameNote(localStorage.token, noteId, pageTitle);
    }
  }
  
  function openSidebar() {
    showSidebar = true;
  }
  
  function closeSidebar() {
    showSidebar = false;
  }

  function initCollaboration() {
    const documentName = `note:${noteId}`;
    const currentUser = get(user);
    
    // 세션별 고유 ID 생성 (브라우저 탭마다 다른 ID)
    const sessionId = crypto.randomUUID();
    
    // 랜덤 색상 생성 함수
    const getRandomColor = () => {
      const colors = [
        '#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', 
        '#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50', 
        '#8bc34a', '#cddc39', '#ffc107', '#ff9800', '#ff5722'
      ];
      return colors[Math.floor(Math.random() * colors.length)];
    };
    
    // 세션별 색상 생성
    const sessionColor = getRandomColor();
    
    provider = new HocuspocusProvider({
      url:
        window.location.hostname === 'localhost'
          ? 'ws://localhost:1234'
          : `ws://${window.location.hostname}:1234`,
      name: documentName,
      token: localStorage.getItem('token'),
      connect: true,
      maxRetries: 10,
      retryDelay: 1000,
      onAuthenticated: () => {
        console.log('협업 서버에 인증됨');
      },
      onSynced: () => {
        console.log('문서 동기화 완료');
      },
      onClose: () => {
        console.log('협업 서버와 연결 끊김');
      },
      onMessage: (message) => {
        console.log('서버 메시지:', message);
      }
    });
    
    const yActiveUsers = provider.document.getMap('activeUsers');
    yActiveUsers.observe(() => {
      activeUsers = Array.from(yActiveUsers.values());
    });
    
    return provider;
  }

  function initEditor(content, provider) {
    const currentUser = get(user);
    
    // 랜덤 색상 생성 함수
    const getRandomColor = () => {
      const colors = [
        '#f44336', // 빨강
        '#e91e63', // 핑크
        '#9c27b0', // 보라
        '#673ab7', // 진보라
        '#3f51b5', // 남색
        '#2196f3', // 파랑
        '#03a9f4', // 하늘
        '#00bcd4', // 청록
        '#009688', // 틸
        '#4caf50', // 초록
        '#8bc34a', // 연두
        '#cddc39', // 라임
        '#ffc107', // 황색
        '#ff9800', // 주황
        '#ff5722'  // 주홍
      ];
      return colors[Math.floor(Math.random() * colors.length)];
    };
    
    // 세션별 색상 생성
    const sessionColor = getRandomColor();
    
    editor = new Editor({
      element: editorElement,
      extensions: [
        ...getExtensions({ bubbleMenuElement, adjustBubbleMenuPosition }),
        // 협업 확장 기능 추가
        Collaboration.configure({
          document: provider.document,
        }),
        CollaborationCursor.configure({
          provider,
          user: {
            name: currentUser?.name || 'Anonymous',
            color: sessionColor, // 세션별 랜덤 색상 적용
            avatar: currentUser?.avatar
          },
        }),
      ],
      content,
      autofocus: true,
      onSelectionUpdate({ editor }) {
        updateEditorState();
      }
    });
    
    return editor;
  }  

  onMount(async () => {
    note = await getNote(noteId);
    if (note && note.title) {
      pageTitle = note.title;
    }
    
    provider = initCollaboration();
    editor = initEditor('', provider);
    
    document.addEventListener('click', closeAllDropdowns);
    window.addEventListener('resize', adjustBubbleMenuPosition);
  });

  onDestroy(() => {
    if (editor) {
      editor.destroy();
    }
    
    if (provider) {
      provider.destroy();
    }
    
    document.removeEventListener('click', closeAllDropdowns);
    window.removeEventListener('resize', adjustBubbleMenuPosition);
  });
</script>

<TopBar {pageTitle} on:titleChange={handleTitleChange} onNewChat={openSidebar} />

<!-- 협업자 목록 표시 -->
<CollaboratorsList users={activeUsers} />

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
    {showColorPicker}
    {showHighlightPicker}
    {showAlignmentOptions}
    {showLinkInput}
    {colorPickerPosition}
    {highlightPickerPosition}
    {alignmentDropdownPosition}
    {linkInputPosition}
    {linkInputValue}
    {setColor}
    {setHighlight}
    {setTextAlignLeft}
    {setTextAlignCenter}
    {setTextAlignRight}
    {applyLink}
    {handleLinkInputKeydown}
  />
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
  .editor-wrapper:focus {
    outline: none;
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

  /* 협업 관련 스타일 */
  :global(.collaboration-cursor__caret) {
    border-left: 1px solid;
    border-right: 1px solid;
    margin-left: -1px;
    margin-right: -1px;
    pointer-events: none;
    position: relative;
    word-break: normal;
  }

  :global(.collaboration-cursor__label) {
    border-radius: 3px 3px 3px 0;
    color: #fff;
    font-size: 12px;
    font-style: normal;
    font-weight: 600;
    left: -1px;
    line-height: normal;
    padding: 0.1rem 0.3rem;
    position: absolute;
    top: -1.4em;
    user-select: none;
    white-space: nowrap;
  }
</style>
