<!-- NoteEditor.svelte -->
<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { Editor } from '@tiptap/core';
	import { Plugin, PluginKey, TextSelection, NodeSelection } from 'prosemirror-state';
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
	import { user } from '$lib/stores';
	import { getNote, renameNote } from '../apis/note';

	// Type declarations
	// Add custom type declaration for HTMLDivElement with cleanupListeners property
	interface HTMLDivElementWithCleanup extends HTMLDivElement {
		cleanupListeners?: () => void;
	}

	interface Note {
		title?: string;
		content?: any;
	}

	interface EditorState {
		bold: boolean;
		italic: boolean;
		underline: boolean;
		strike: boolean;
		textStyle: boolean;
		highlight: boolean;
		link: boolean;
		textAlignLeft: boolean;
		textAlignCenter: boolean;
		textAlignRight: boolean;
	}

	interface Position {
		x: number;
		y: number;
	}

	interface ActiveUser {
		id: string;
		name: string;
		color: string;
		avatar?: string;
	}

	// Editor and UI state variables
	let editor: Editor | null = null;
	let editorElement: HTMLDivElementWithCleanup | null = null;
	let pageTitle = '';
	let showSidebar = false;
	let note: Note = {};
	let manualTitleEdited = false;
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let bubbleMenuElement: HTMLElement | null = null;
	let isLineMenuOpen = false;

	// Collaboration variables
	let provider: HocuspocusProvider | null = null;
	let activeUsers: ActiveUser[] = [];

	// Editor state tracking
	let editorState: EditorState = {
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

	// Position variables for dropdowns
	let colorPickerPosition: Position = { x: 0, y: 0 };
	let highlightPickerPosition: Position = { x: 0, y: 0 };
	let alignmentDropdownPosition: Position = { x: 0, y: 0 };

	// Link related variables
	let showLinkInput = false;
	let linkInputPosition: Position = { x: 0, y: 0 };
	let linkInputValue = '';

	// UI state variables
	let showColorPicker = false;
	let showHighlightPicker = false;
	let showAlignmentOptions = false;

	/**
	 * Adjusts the position of the bubble menu to ensure it stays within viewport
	 */
	function adjustBubbleMenuPosition(): void {
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

	/**
	 * Updates the editor state based on current selection and formatting
	 */
	function updateEditorState(): void {
		if (!editor) return;

		// Hide bubble menu if line menu is active or selection is empty
		if (isLineMenuOpen) {
			if (bubbleMenuElement) {
				bubbleMenuElement.style.visibility = 'hidden';
				bubbleMenuElement.style.display = 'none';
			}
		} else if (editor.state.selection.empty) {
			// Selection is empty
			if (bubbleMenuElement) {
				bubbleMenuElement.style.visibility = 'hidden';
				bubbleMenuElement.style.display = 'none';
			}
		} else {
			// Selection exists and line menu is not active
			if (bubbleMenuElement) {
				bubbleMenuElement.style.visibility = 'visible';
				bubbleMenuElement.style.display = 'flex';
				// Ensure position adjustment when bubble menu is displayed
				setTimeout(adjustBubbleMenuPosition, 0);
			}
		}

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

	/**
	 * Forces the bubble menu to display if conditions are met
	 */
	function forceBubbleMenuDisplay(): void {
		if (!bubbleMenuElement || !editor || isLineMenuOpen || editor.state.selection.empty) return;
		
		bubbleMenuElement.style.visibility = 'visible';
		bubbleMenuElement.style.display = 'flex';
		adjustBubbleMenuPosition();
		updateEditorState();
	}

	/**
	 * Translates selected text using an API
	 */
	async function translateSelectedText(): Promise<void> {
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

	// Text formatting functions
	function toggleBold(): void {
		if (!editor) return;
		editor.chain().focus().toggleBold().run();
		updateEditorState();
	}

	function toggleItalic(): void {
		if (!editor) return;
		editor.chain().focus().toggleItalic().run();
		updateEditorState();
	}

	function toggleUnderline(): void {
		if (!editor) return;
		editor.chain().focus().toggleUnderline().run();
		updateEditorState();
	}

	function toggleStrike(): void {
		if (!editor) return;
		editor.chain().focus().toggleStrike().run();
		updateEditorState();
	}

	function toggleColorPicker(event: MouseEvent): void {
		event.stopPropagation();
		const buttonRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
		colorPickerPosition = {
			x: buttonRect.left,
			y: buttonRect.bottom + 10
		};

		showColorPicker = !showColorPicker;
		showHighlightPicker = false;
		showAlignmentOptions = false;
	}

	function toggleHighlightPicker(event: MouseEvent): void {
		event.stopPropagation();
		toggleHighlight();
	}

	function toggleHighlight(): void {
		if (!editor) return;

		const isHighlighted = editor.isActive('highlight');

		if (isHighlighted) {
			editor.chain().focus().unsetHighlight().run();
		} else {
			editor.chain().focus().setHighlight({ color: '#FFFF00' }).run();
		}

		updateEditorState();
	}

	function toggleAlignmentOptions(event: MouseEvent): void {
		event.stopPropagation();
		const buttonRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
		alignmentDropdownPosition = {
			x: buttonRect.left,
			y: buttonRect.bottom + 10
		};

		showAlignmentOptions = !showAlignmentOptions;
		showColorPicker = false;
		showHighlightPicker = false;
	}

	function setColor(color: string): void {
		if (!editor) return;
		editor.chain().focus().setColor(color).run();
		showColorPicker = false;
		updateEditorState();
	}

	function setHighlight(color: string): void {
		if (!editor) return;
		editor.chain().focus().toggleHighlight({ color }).run();
		showHighlightPicker = false;
		updateEditorState();
	}

	function setTextAlignLeft(): void {
		if (!editor) return;
		editor.chain().focus().setTextAlign('left').run();
		checkAlignmentState();
		updateEditorState();
	}

	function setTextAlignCenter(): void {
		if (!editor) return;
		editor.chain().focus().setTextAlign('center').run();
		checkAlignmentState();
		updateEditorState();
	}

	function setTextAlignRight(): void {
		if (!editor) return;
		editor.chain().focus().setTextAlign('right').run();
		checkAlignmentState();
		updateEditorState();
	}

	function checkAlignmentState(): void {
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

	function removeFormat(): void {
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

	function setLink(): void {
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

		if (!bubbleMenuElement) return;
		
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

	function applyLink(): void {
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

	function handleLinkInputKeydown(event: KeyboardEvent): void {
		if (event.key === 'Enter') {
			event.preventDefault();
			applyLink();
		} else if (event.key === 'Escape') {
			event.preventDefault();
			cancelLinkInput();
		}
	}

	function cancelLinkInput(): void {
		showLinkInput = false;
		linkInputValue = '';
	}

	function closeAllDropdowns(): void {
		showColorPicker = false;
		showHighlightPicker = false;
		showAlignmentOptions = false;
	}

	function handleTitleChange(e: CustomEvent<string>): void {
		pageTitle = e.detail;
		manualTitleEdited = true;
		if (editor && noteId) {
			const token = localStorage.getItem('token') || '';
			renameNote(token, noteId, pageTitle);
		}
	}

	function openSidebar(): void {
		showSidebar = true;
	}

	function closeSidebar(): void {
		showSidebar = false;
	}

	/**
	 * Sets up collaboration features for the editor
	 */
	function setupCollaboration(): HocuspocusProvider {
		const documentName = `note:${noteId}`;
		const currentUser = get(user);

		const getRandomColor = (): string => {
			const colors = [
				'#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
				'#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50',
				'#8bc34a', '#cddc39', '#ffc107', '#ff9800', '#ff5722'
			];
			return colors[Math.floor(Math.random() * colors.length)];
		};

		const sessionColor = getRandomColor();
		const token = localStorage.getItem('token') || '';

		const providerInstance = new HocuspocusProvider({
			url: window.location.hostname === 'localhost'
				? 'ws://localhost:1234'
				: `ws://${window.location.hostname}:1234`,
			name: documentName,
			token: token,
			connect: true,
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

		const yActiveUsers = providerInstance.document.getMap('activeUsers');
		yActiveUsers.observe(() => {
			activeUsers = Array.from(yActiveUsers.values()) as ActiveUser[];
		});

		return providerInstance;
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
							const pluginState = this.getState(state);
							const highlightedPos = pluginState ? pluginState.highlightedPos : null;
							const decorations: any[] = [];
							
							doc.descendants((node, pos) => {
								if (node.isBlock && !node.isText) {
									// Add class based on highlight state
									const classes = ['line-block'];
									if (highlightedPos === pos) {
										classes.push('line-highlight');
									}
									const blockDeco = Decoration.node(pos, pos + node.nodeSize, {
										class: classes.join(' ')
									});
									decorations.push(blockDeco);
				
									// Create line menu icon
									const lineIcon = document.createElement('div');
									lineIcon.className = 'line-icon';
									lineIcon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="6" r="1" fill="currentColor"/><circle cx="12" cy="18" r="1" fill="currentColor"/></svg>';
				
									// Add click event listener
									lineIcon.addEventListener('click', (e) => {
										e.preventDefault();
										e.stopPropagation();
										try {
											console.log('라인 메뉴 아이콘 클릭됨', { node, pos });
											const editorInstance = extensionThis.editor || editor;
											if (!editorInstance) return;
											
											isLineMenuOpen = true;
									
											const currentPluginState = this.getState(editorInstance.state);
											if (!currentPluginState) return;
											
											const newHighlightedPos = currentPluginState.highlightedPos === pos ? null : pos;
											const transaction = editorInstance.state.tr
												.setSelection(NodeSelection.create(editorInstance.state.doc, pos))
												.setMeta('toggleLineHighlight', newHighlightedPos);
											editorInstance.view.dispatch(transaction);
									
											showLineMenu(
												e.clientX, 
												e.clientY, 
												editorInstance, 
												node, 
												pos,
												() => {
													console.log('라인 메뉴 종료: 텍스트 선택 복구');
													// Reset line menu state
													isLineMenuOpen = false;
													
													// Force text selection to trigger bubble menu
													try {
														// Check if node has content
														const nodeContent = node.textContent || '';
														if (nodeContent.length > 0) {
															// Create text selection if node has content
															const startPos = pos + 1; // After node start
															const endPos = Math.min(startPos + 5, pos + node.nodeSize - 1); // Max 5 chars or node end
															
															// Create and apply text selection
															const newSelection = TextSelection.create(editorInstance.state.doc, startPos, endPos);
															editorInstance.view.dispatch(editorInstance.state.tr.setSelection(newSelection));
															
															// Force bubble menu display
															setTimeout(() => {
																forceBubbleMenuDisplay();
															}, 50);
														} else {
															// Handle empty node
															console.log('노드가 비어있어 다른 방식으로 선택 생성 시도');
															// Try moving to next node
															const nextPos = pos + node.nodeSize;
															if (nextPos < editorInstance.state.doc.content.size) {
																const newSelection = TextSelection.create(editorInstance.state.doc, nextPos, nextPos + 1);
																editorInstance.view.dispatch(editorInstance.state.tr.setSelection(newSelection));
																
																setTimeout(() => {
																	forceBubbleMenuDisplay();
																}, 50);
															}
														}
													} catch (error) {
														console.error('텍스트 선택 생성 중 오류:', error);
													}
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

	/**
	 * Initializes the editor with content and collaboration features
	 */
	function initEditor(content: any, provider: HocuspocusProvider): Editor {
		const currentUser = get(user);

		const getRandomColor = (): string => {
			const colors = [
				'#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
				'#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50',
				'#8bc34a', '#cddc39', '#ffc107', '#ff9800', '#ff5722'
			];
			return colors[Math.floor(Math.random() * colors.length)];
		};
		const sessionColor = getRandomColor();

		if (content && typeof content === 'object' && !Array.isArray(content)) {
			const updateArray = new Uint8Array(Object.values(content));
			Y.applyUpdate(provider.document, updateArray);
		}

		if (!editorElement) return null as unknown as Editor;

		const editorInstance = new Editor({
			element: editorElement,
			extensions: [
				...getExtensions({ 
					bubbleMenuElement: bubbleMenuElement as HTMLElement, 
					adjustBubbleMenuPosition 
				}),
				Collaboration.configure({
					document: provider.document
				}),
				CollaborationCursor.configure({
					provider,
					user: {
						name: currentUser?.name || 'Anonymous',
						color: sessionColor
					}
				}),
				lineMenuExtension
			],
			content: '',
			autofocus: true,
			onSelectionUpdate({ editor }) {
				// Update editor state when selection changes
				setTimeout(() => {
					updateEditorState();
				}, 0);
			}
		});
		return editorInstance;
	}

	onMount(async () => {
		try {
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
			
			// Initialize bubble menu state after editor setup
			setTimeout(() => {
				updateEditorState();
			}, 100);
		} catch (error) {
			console.error('에디터 초기화 중 오류:', error);
		}
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
	<!-- RightSidebar component is not available or not needed -->
{/if}

<style>
	:global(.line-highlight) {
		background-color: #ffff99; /* 원하는 하이라이트 색상으로 수정 가능 */
	}

	:global(.tippy-box[data-theme~='bubble-menu-theme']) {
		background-color: transparent !important;
		box-shadow: none !important;
		transform: translateY(-15px) !important;
		visibility: visible !important;
		display: flex !important;
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
