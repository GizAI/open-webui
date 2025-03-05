<!-- NoteEditor.svelte -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
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
	import { createAddIcon, showAddMenu } from './LineMenu.svelte'; // Import the functions from LineMenu
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

	/* 기존 코드에서 "굵게/이탤릭"을 넣었던 라인 메뉴 확장을 확장/보강 */
	const LineMenuExtension = Extension.create({
		name: 'lineMenuExtension',

		addProseMirrorPlugins() {
			const extensionThis = this;
			return [
				new Plugin({
					key: new PluginKey('lineMenuExtension'),
					state: {
						init(_, { doc }) {
							return DecorationSet.empty;
						},
						apply(tr, oldDecorationSet) {
							const decorations = [];

							tr.doc.descendants((node, pos) => {
								// 블록 노드(문단, 헤딩 등)만 대상
								if (node.isBlock) {
									// 블록 노드에 line-block 클래스 추가
									const blockDeco = Decoration.node(pos, pos + node.nodeSize, {
										class: 'line-block'
									});
									decorations.push(blockDeco);
									
									// + 버튼 아이콘 추가
									const addDeco = Decoration.widget(
										pos + node.nodeSize - 1,
										() => {
											// LineMenu 컴포넌트의 createAddIcon 함수 사용
											const addIcon = createAddIcon();
											
											// 아이콘 자체에 마우스 오버 이벤트 추가
											addIcon.addEventListener('mouseover', () => {
												addIcon.style.backgroundColor = 'rgba(0, 0, 0, 0.1)';
												addIcon.style.opacity = '1';
											});
											
											addIcon.addEventListener('mouseout', () => {
												addIcon.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
												if (!document.querySelector('.line-block:hover')) {
													addIcon.style.opacity = '0';
												}
											});
											
											// 클릭 이벤트
											addIcon.addEventListener('click', (e) => {
												e.preventDefault();
												e.stopPropagation();
												
												// LineMenu 컴포넌트의 showAddMenu 함수 사용
												showAddMenu(
													e.clientX,
													e.clientY,
													extensionThis.editor,
													pos + node.nodeSize
												);
											});
											
											// 아이콘이 생성된 후 부모 요소에 이벤트 리스너 추가
											setTimeout(() => {
												const parentBlock = addIcon.closest('.line-block') || 
													document.querySelector(`.line-block[data-node-id="${pos}"]`) ||
													addIcon.parentElement;
												
												if (parentBlock) {
													const handleParentHover = () => {
														addIcon.style.opacity = '1';
													};
													
													const handleParentLeave = () => {
														if (!addIcon.matches(':hover')) {
															addIcon.style.opacity = '0';
														}
													};
													
													parentBlock.addEventListener('mouseover', handleParentHover);
													parentBlock.addEventListener('mouseout', handleParentLeave);
													
													// 클린업 함수 설정
													// @ts-ignore
													addIcon.cleanupListeners = () => {
														parentBlock.removeEventListener('mouseover', handleParentHover);
														parentBlock.removeEventListener('mouseout', handleParentLeave);
													};
												}
											}, 0);
											
											return addIcon;
										},
										{ side: 1 }
									);
									decorations.push(addDeco);
								}
							});
							return DecorationSet.create(tr.doc, decorations);
						}
					},
					props: {
						decorations(state) {
							return this.getState(state);
						}
					}
				})
			];
		}
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
				LineMenuExtension
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

	
	#line-menu-popup button {
		border: none;
		background: transparent;
		cursor: pointer;
		width: 100%;
		text-align: left;
		padding: 6px 8px;
		font-size: 14px;
		border-radius: 4px;
		color: #333;
		display: flex;
		align-items: center;
	}

	#line-menu-popup button:hover {
		background: #f5f5f5;
	}

	
	.line-icon {
		opacity: 0; 
		transition: opacity 0.2s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		position: absolute;
		left: -24px;
		top: 50%;
		transform: translateY(-50%);
		padding: 4px;
		background-color: rgba(0, 0, 0, 0.05);
		border-radius: 4px;
		z-index: 10;
		width: 18px;
		height: 18px;
	}

	.line-icon:hover {
		background-color: rgba(0, 0, 0, 0.1);
		opacity: 1 !important;
	}

	.line-icon-dot {
		width: 4px;
		height: 4px;
		border-radius: 50%;
		background-color: #666;
	}

	.line-block {
		position: relative;
		margin-left: 10px;
		padding-left: 5px;
	}

	.line-block:hover .line-icon {
		opacity: 1;
	}
	
	/* 추가: 라인 블록 호버 스타일 */
	.line-block {
		border-radius: 3px;
		transition: background-color 0.2s ease;
	}
	
	.line-block:hover {
		background-color: rgba(0, 0, 0, 0.02);
	}

</style>
