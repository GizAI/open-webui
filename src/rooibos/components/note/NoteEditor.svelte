<!-- NoteEditor.svelte -->
<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { Editor } from '@tiptap/core';
	import { Plugin, PluginKey } from 'prosemirror-state';
	import { Decoration, DecorationSet } from 'prosemirror-view';
	import { Extension } from '@tiptap/core';
	import { Collaboration } from '@tiptap/extension-collaboration';
	import { CollaborationCursor } from '@tiptap/extension-collaboration-cursor';
	import * as Y from 'yjs';
	import { getExtensions } from './tiptapExtension';
	import TopBar from './TopBar.svelte';
	import BubbleMenu from './BubbleMenu.svelte';
	import CollaboratorsList from './CollaboratorsList.svelte';
	import { showLineMenu } from './LineMenu.svelte';
	import { HocuspocusProvider } from '@hocuspocus/provider';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';
	import { user} from '$lib/stores';
	import { getNote } from '../apis/note';

	// Add custom type declaration for HTMLDivElement with cleanupListeners property
	declare global {
		interface HTMLDivElement {
			cleanupListeners?: () => void;
		}
	}

	/**
	 * @typedef {Object} Note
	 * @property {string} [title] - The title of the note.
	 * @property {any} [content] - The content of the note.
	 */

	/**
	 * @typedef {Object} EditorState
	 * @property {boolean} bold - Whether the text is bold.
	 * @property {boolean} italic - Whether the text is italic.
	 * @property {boolean} underline - Whether the text is underlined.
	 * @property {boolean} strike - Whether the text is struck through.
	 * @property {boolean} textStyle - Whether the text has a specific style.
	 * @property {boolean} highlight - Whether the text is highlighted.
	 * @property {boolean} link - Whether the text is linked.
	 * @property {boolean} textAlignLeft - Whether the text is left-aligned.
	 * @property {boolean} textAlignCenter - Whether the text is center-aligned.
	 * @property {boolean} textAlignRight - Whether the text is right-aligned.
	 */

	/**
	 * @typedef {Object} Position
	 * @property {number} x - The x-coordinate of the position.
	 * @property {number} y - The y-coordinate of the position.
	 */

	let editor;
	let editorElement;
	let pageTitle = '';
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
				.then((res) => res.json())
				.then((data) => data.translatedText);

			editor.chain().focus().deleteSelection().insertContent(translatedText).run();
			updateEditorState();
		} catch (error) {
			console.error('번역 중 오류 발생:', error);
		}
	}

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

			console.log('정렬 상태:', {
				왼쪽: isLeftAligned,
				가운데: isCenterAligned,
				오른쪽: isRightAligned
			});
		} catch (error) {
			console.error('정렬 상태 확인 중 오류:', error);
		}
	}

	function removeFormat() {
		if (!editor) return;

		editor.chain().focus().unsetAllMarks().clearNodes().setTextAlign('left').run();

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

		if (hasLink) {
			editor.chain().focus().unsetLink().run();
			updateEditorState();
			return;
		}

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

		const { from, to } = editor.state.selection;
		if (from === to) {
			editor
				.chain()
				.focus()
				.insertContent(`<a href="${linkInputValue}" target="_blank">${linkInputValue}</a>`)
				.run();
		} else {
			editor.chain().focus().unsetLink().setLink({ href: linkInputValue, target: '_blank' }).run();
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

	function setupCollaboration() {
		const documentName = `note:${noteId}`;
		const currentUser = get(user);

		const sessionId = crypto.randomUUID();

		const getRandomColor = () => {
			const colors = [
				'#f44336',
				'#e91e63',
				'#9c27b0',
				'#673ab7',
				'#3f51b5',
				'#2196f3',
				'#03a9f4',
				'#00bcd4',
				'#009688',
				'#4caf50',
				'#8bc34a',
				'#cddc39',
				'#ffc107',
				'#ff9800',
				'#ff5722'
			];
			return colors[Math.floor(Math.random() * colors.length)];
		};

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

	// Line menu extension
	const lineMenuExtension = Extension.create({
   name: 'lineMenu',
   addProseMirrorPlugins() {
     const extensionThis = this;
     return [
       new Plugin({
         key: new PluginKey('lineMenu'),
         state: {
           init() {
             return { highlightedPos: null };
           },
           apply(tr, value) {
             const highlight = tr.getMeta('toggleLineHighlight');
             if (highlight !== undefined) {
               return { highlightedPos: highlight };
             }
             return value;
           }
         },
         props: {
           decorations(state) {
             const { doc } = state;
             const { highlightedPos } = this.getState(state);
             const decorations = [];
             doc.descendants((node, pos) => {
               if (node.isBlock && !node.isText) {
                 // 하이라이트 상태에 따라 클래스 추가
                 const classes = ['line-block'];
                 if (highlightedPos === pos) {
                   classes.push('line-highlight');
                 }
				 const blockDeco = Decoration.node(pos, pos + node.nodeSize, {
                   class: classes.join(' ')
                 });
                 decorations.push(blockDeco);
 
                 // 라인 메뉴 아이콘 생성
                 const lineIcon = document.createElement('div');
                 lineIcon.className = 'line-icon';
                 lineIcon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="6" r="1" fill="currentColor"/><circle cx="12" cy="18" r="1" fill="currentColor"/></svg>';
 
                 // 클릭 이벤트 리스너 추가
                 lineIcon.addEventListener('click', (e) => {
                   e.preventDefault();
                   e.stopPropagation();
                   
                   try {
                     console.log('라인 메뉴 아이콘 클릭됨', { node, pos });
                     const editorInstance = extensionThis.editor || editor;
                     // 현재 하이라이트 상태 토글
                     const currentPluginState = this.getState(editorInstance.state);
                     const newHighlightedPos = currentPluginState.highlightedPos === pos ? null : pos;
                     editorInstance.view.dispatch(editorInstance.state.tr.setMeta('toggleLineHighlight', newHighlightedPos));
 
                     showLineMenu(
                       e.clientX, 
                       e.clientY, 
                       editorInstance, 
                       node, 
                       pos,
                       () => {
                         console.log('사이드바 열기 콜백');
                       }
                     );
                   } catch (error) {
                     console.error('라인 메뉴 표시 중 오류:', error);
                   }
                 });
                 
                 const decorationWidget = Decoration.widget(pos, lineIcon, {
                   side: -1,
                   key: `line-menu-${pos}`,
                 });
                 decorations.push(decorationWidget);
               }
               return true;
             });
             return DecorationSet.create(doc, decorations);
           }
         },
       }),
     ];
   },
 });

	function initEditor(content, provider) {
		const currentUser = get(user);

		const getRandomColor = () => {
			const colors = [
				'#f44336',
				'#e91e63',
				'#9c27b0',
				'#673ab7',
				'#3f51b5',
				'#2196f3',
				'#03a9f4',
				'#00bcd4',
				'#009688',
				'#4caf50',
				'#8bc34a',
				'#cddc39',
				'#ffc107',
				'#ff9800',
				'#ff5722'
			];
			return colors[Math.floor(Math.random() * colors.length)];
		};
		const sessionColor = getRandomColor();

		if (content && typeof content === 'object' && !Array.isArray(content)) {
			const updateArray = new Uint8Array(Object.values(content));
			Y.applyUpdate(provider.document, updateArray);
		}

		editor = new Editor({
			element: editorElement,
			extensions: [
				...getExtensions({ bubbleMenuElement, adjustBubbleMenuPosition }),
				Collaboration.configure({
					document: provider.document
				}),
				CollaborationCursor.configure({
					provider,
					user: {
						name: currentUser?.name || 'Anonymous',
						color: sessionColor,
						avatar: currentUser?.avatar
					}
				}),
				lineMenuExtension
			],
			content: '',
			autofocus: true,
			onSelectionUpdate({ editor }) {
				updateEditorState();
			}
		});
		return editor;
	}

	onMount(async () => {
		note = await getNote(noteId);
		if (note.title) {
			pageTitle = note.title;
		} else {
			pageTitle = '새 페이지';
		}

		provider = setupCollaboration();

		let storedUpdate = note.content;
		if (storedUpdate && typeof storedUpdate === 'string') {
			try {
				storedUpdate = JSON.parse(storedUpdate);
			} catch (e) {
				console.error('노트 content 파싱 오류:', e);
			}
		}

		if (storedUpdate && typeof storedUpdate === 'object' && !Array.isArray(storedUpdate)) {
			const updateArray = new Uint8Array(Object.values(storedUpdate));
			Y.applyUpdate(provider.document, updateArray);
		}

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

<CollaboratorsList users={activeUsers} />

<div class="notion-page-container">
	<div class="editor-wrapper" bind:this={editorElement}></div>

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
		bind:linkInputValue
		{setColor}
		{setHighlight}
		{setTextAlignLeft}
		{setTextAlignCenter}
		{setTextAlignRight}
		{applyLink}
		{handleLinkInputKeydown}
	/>
</div>

{#if showSidebar && false}
	<RightSidebar on:close={closeSidebar} />
{/if}

<style>
	:global(.line-highlight) {
	background-color: #ffff99; /* 원하는 하이라이트 색상으로 수정 가능 */
}


	.notion-page-container {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
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
		border-radius: 4px;
		color: #fff;
		font-size: 14px;
		font-style: normal;
		font-weight: 600;
		padding: 0.1rem 0.3rem;
		position: absolute;
		top: -1.8em;
		left: 0;
		user-select: none;
		white-space: nowrap;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
		transform: translateY(-2px);
		z-index: 100;
	}
</style>
