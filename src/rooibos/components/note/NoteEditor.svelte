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
	import { get } from 'svelte/store';
	import { user } from '$lib/stores';

	const dispatch = createEventDispatcher();

	// HocuspocusProvider 타입 확장
	interface ExtendedHocuspocusProvider extends HocuspocusProvider {
		websocket?: WebSocket;
	}

	// ProseMirror Node 타입 확장
	interface ExtendedNode extends Node {
		parent?: any;
		type?: {
			name?: string;
		};
	}

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
		heading3: boolean; 
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

	export let initialTitle: string = '';
	export let initialContent: any = '';
	export let selectedFile: any;

	let pageTitle = initialTitle || '새 노트';

	function getFileId(): string {
		if (!selectedFile) return "";
		return selectedFile.id || "";
	}

	function getOriginalFilename(): string {
		if (!selectedFile) return "";
		return selectedFile.filename || selectedFile.name || "";
	}

	let editor: Editor | null = null;
	let editorElement: HTMLDivElementWithCleanup | null = null;	
	let showSidebar = false;
	let note: Note = {};
	let manualTitleEdited = false;
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let bubbleMenuElement: HTMLElement | null = null;
	let isLineMenuOpen = false;

	let provider: ExtendedHocuspocusProvider | null = null;
	let activeUsers: ActiveUser[] = [];
	let websocketCheckInterval: ReturnType<typeof setInterval> | null = null;

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
		textAlignRight: false,
		heading3: false
	};

	const { id: noteId } = selectedFile;

	let colorPickerPosition: Position = { x: 0, y: 0 };
	let highlightPickerPosition: Position = { x: 0, y: 0 };
	let alignmentDropdownPosition: Position = { x: 0, y: 0 };

	let showLinkInput = false;
	let linkInputPosition: Position = { x: 0, y: 0 };
	let linkInputValue = '';

	let showColorPicker = false;
	let showHighlightPicker = false;
	let showAlignmentOptions = false;

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

	function updateEditorState(): void {
		if (!editor) return;

		if (isLineMenuOpen) {
			if (bubbleMenuElement) {
				bubbleMenuElement.style.visibility = 'hidden';
				bubbleMenuElement.style.display = 'none';
			}
		} else if (editor.state.selection.empty) {
			if (bubbleMenuElement) {
				bubbleMenuElement.style.visibility = 'hidden';
				bubbleMenuElement.style.display = 'none';
			}
		} else {
			if (bubbleMenuElement) {
				bubbleMenuElement.style.visibility = 'visible';
				bubbleMenuElement.style.display = 'flex';
				
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
			textAlignRight: editor.isActive({ textAlign: 'right' }),
			heading3: editor.isActive('heading', { level: 3 })
		};
	}

	 function forceBubbleMenuDisplay(): void {
		if (!bubbleMenuElement || !editor || isLineMenuOpen) return;
		if (!(editor.state.selection instanceof TextSelection) || editor.state.selection.empty) return;
		
		bubbleMenuElement.style.visibility = 'visible';
		bubbleMenuElement.style.display = 'flex';
		adjustBubbleMenuPosition();
		updateEditorState();
	}

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
		
		const { from, to } = editor.state.selection;
		
		editor.chain()
			.focus()
			.unsetTextAlign()
			.setTextAlign('left')
			.run();
		
		editor.commands.setTextSelection({ from, to });
		
		showAlignmentOptions = false;
		checkAlignmentState();
		updateEditorState();		
	}

	function setTextAlignCenter(): void {
		if (!editor) return;
		
		const { from, to } = editor.state.selection;
		
		editor.chain()
			.focus()
			.unsetTextAlign()
			.setTextAlign('center')
			.run();
		
		editor.commands.setTextSelection({ from, to });
		
		showAlignmentOptions = false;
		checkAlignmentState();
		updateEditorState();		
	}

	function setTextAlignRight(): void {
		if (!editor) return;
		
		const { from, to } = editor.state.selection;
		
		editor.chain()
			.focus()
			.unsetTextAlign()
			.setTextAlign('right')
			.run();
		
		editor.commands.setTextSelection({ from, to });
		
		showAlignmentOptions = false;
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
			textAlignRight: false,
			heading3: false
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
	
		const lineMenu = document.getElementById('line-menu-popup');
		if (lineMenu) {
			lineMenu.remove();
			isLineMenuOpen = false;
		}
	
		if (editor) {
			editor.view.dispatch(editor.state.tr.setMeta('toggleLineHighlight', null));
		}
	}

	function closeLineMenu(e: MouseEvent): void {
		if (!e.target) return;
		
		const target = e.target as HTMLElement;
		const isLineIconClick = target.closest('.line-icon') !== null;
		const isLineMenuClick = target.closest('#line-menu-popup') !== null;
		
		if (!isLineIconClick && !isLineMenuClick) {
			const lineMenu = document.getElementById('line-menu-popup');
			if (lineMenu) {
				lineMenu.remove();
				isLineMenuOpen = false;
				
				setTimeout(() => {
					forceBubbleMenuDisplay();
				}, 50);
			}
		}
	}

	function handleTitleChange(e: CustomEvent<string>): void {
		pageTitle = e.detail;
		manualTitleEdited = true;
		
		if (selectedFile) {
			if (selectedFile.name) {
				selectedFile.name = pageTitle;
			}
			if (selectedFile.filename) {
				const extension = selectedFile.filename.substring(selectedFile.filename.lastIndexOf('.'));
				selectedFile.filename = pageTitle + (pageTitle.endsWith(extension) ? '' : extension);
			}
			if (selectedFile.meta && selectedFile.meta.name) {
				selectedFile.meta.name = pageTitle;
			}
		}
		
		dispatch('titleChange', pageTitle);
	}

	function openSidebar(): void {
		showSidebar = true;
	}

	function closeSidebar(): void {
		showSidebar = false;
	}

	function setupCollaboration(): ExtendedHocuspocusProvider {
		const documentName = `note:${noteId}`;
		const currentUser = get(user);

		const token = localStorage.getItem('token') || '';
		
		const providerInstance = new HocuspocusProvider({
			url: window.location.hostname === 'localhost'
				? 'ws://localhost:8444'
				: 'wss://hocuspocus.conting.ai/ws',
			name: documentName,
			token: token,
			connect: true,
			onAuthenticated: () => {
				console.log('Collaboration server authenticated successfully');
			},
			onSynced: () => {
				console.log('Document synchronized successfully');
			},
			onClose: () => {
				console.error('Connection closed:');
			},
			onMessage: (message) => {
			}
		});

		if (providerInstance.websocket) {
			providerInstance.websocket.addEventListener('error', (error) => {
				console.error('Raw WebSocket error event:', error);
			});
		}

		startWebsocketCheck(providerInstance);

		const yActiveUsers = providerInstance.document.getMap('activeUsers');
		yActiveUsers.observe(() => {
			activeUsers = Array.from(yActiveUsers.values()) as ActiveUser[];
		});

		return providerInstance;
	}

	function startWebsocketCheck(providerInstance: ExtendedHocuspocusProvider): void {
		if (websocketCheckInterval) {
			clearInterval(websocketCheckInterval);
		}
		
		websocketCheckInterval = setInterval(() => {
			if (providerInstance.websocket) {
				const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
				console.log('WebSocket status:', states[providerInstance.websocket.readyState]);
				
				if (providerInstance.websocket.readyState === WebSocket.CLOSED) {
					console.log('WebSocket is closed. Attempting to reconnect...');
					providerInstance.connect();
				}
			} 
		}, 10000);
	}

	function stopWebsocketCheck(): void {
		if (websocketCheckInterval) {
			clearInterval(websocketCheckInterval);
			websocketCheckInterval = null;
		}
	}

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
									if (node.type.name === 'taskItem') {
										return true;
									}
									
									if (node.type.name === 'listItem') {
										return true;
									}
									
									if (node.type.name === 'bulletList' || node.type.name === 'orderedList') {
										return true;
									}
									
									if (node.type.name === 'taskList') {
										return true;
									}
									
									if ((node as ExtendedNode).parent && (
										(node as ExtendedNode).parent.type?.name === 'bulletList' || 
										(node as ExtendedNode).parent.type?.name === 'orderedList' || 
										(node as ExtendedNode).parent.type?.name === 'taskList'
									)) {
										return true;
									}
									
									const classes = ['line-block'];
									if (highlightedPos === pos) {
										classes.push('line-highlight');
									}
									const blockDeco = Decoration.node(pos, pos + node.nodeSize, {
										class: classes.join(' '),
										'data-pos': pos.toString()
									});
									decorations.push(blockDeco);
				
									const lineIcon = document.createElement('div');
									lineIcon.className = 'line-icon';
									lineIcon.setAttribute('data-pos', pos.toString());
									lineIcon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="6" r="1" fill="currentColor"/><circle cx="12" cy="18" r="1" fill="currentColor"/></svg>';
			
									if (node.type.name === 'heading' && node.attrs.level === 1) {
										lineIcon.classList.add('heading1-line-icon');
									}

									if (node.type.name === 'heading' && node.attrs.level === 2) {
										lineIcon.classList.add('heading2-line-icon');
									}

									if (node.type.name === 'heading' && node.attrs.level === 3) {
										lineIcon.classList.add('heading3-line-icon');
									}
									
									lineIcon.addEventListener('click', (e) => {
										e.preventDefault();
										e.stopPropagation();
										
										try {
											const editorInstance = extensionThis.editor || editor;
											if (!editorInstance) return;
											
											const existingMenu = document.getElementById('line-menu-popup');
											if (existingMenu) {
												existingMenu.remove();
												isLineMenuOpen = false;
											}
											
											if (isLineMenuOpen && editorInstance.state.selection instanceof NodeSelection && 
												editorInstance.state.selection.from === pos) {
												isLineMenuOpen = false;
												return;
											}
											
											isLineMenuOpen = true;
											
											const newHighlightedPos = pos;
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
													isLineMenuOpen = false;
													setTimeout(() => {
														forceBubbleMenuDisplay();
													}, 50);
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

	function initEditor(content: any, provider: ExtendedHocuspocusProvider): Editor {
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
			content: typeof content === 'string' ? content : '',
			autofocus: true,
			onSelectionUpdate({ editor }) {
				setTimeout(() => {
					updateEditorState();
				}, 0);
			},
			onUpdate({ editor }) {
				dispatch('change', editor.getHTML());
			}
		});
		return editorInstance;
	}

	onMount(async () => {
	try {
		

		provider = setupCollaboration();

		let storedUpdate = initialContent;
		if (storedUpdate && typeof storedUpdate === 'string') {
			if (storedUpdate.trim().startsWith('<') && storedUpdate.trim().endsWith('>')) {
				console.log('HTML content detected');
			} else {
				try {
					storedUpdate = JSON.parse(storedUpdate);
				} catch (e) {
					console.log('노트 content 파싱 오류:', e);
				}
			}
		}

		if (storedUpdate && typeof storedUpdate === 'object' && !Array.isArray(storedUpdate)) {
			const updateArray = new Uint8Array(Object.values(storedUpdate));
			Y.applyUpdate(provider.document, updateArray);
		}

		editor = initEditor(storedUpdate, provider);

		if (typeof storedUpdate === 'string') {
			const yXmlFragment = provider.document.getXmlFragment('prosemirror');
			if (yXmlFragment.length === 0) {
				provider.on('synced', () => {
					if (editor) {
						editor.commands.setContent(storedUpdate);
					}
				});
			}
		}

	console.log('Editor 생성 완료:', editor);
	console.log('Editor 명령어:', editor?.commands);

	document.addEventListener('click', closeAllDropdowns);
	window.addEventListener('resize', adjustBubbleMenuPosition);
	
	document.addEventListener('click', closeLineMenu);
	
	if (editorElement) {
		const handleEditorClick = (e: MouseEvent) => {
			if (!e.target) return;
			
			const target = e.target as HTMLElement;
			const isLineIconClick = target.closest('.line-icon') !== null;
			const isLineMenuClick = target.closest('#line-menu-popup') !== null;

			if (window.innerWidth <= 768) {
				document.querySelectorAll('.line-icon.visible').forEach(icon => icon.classList.remove('visible'));
				
				const lineBlock = target.closest('.line-block');
				
				if (lineBlock) {
					const blockPos = lineBlock.getAttribute('data-pos');
					const lineIcon = document.querySelector(`.line-icon[data-pos="${blockPos}"]`);
					if (lineIcon) {
						lineIcon.classList.add('visible');
					}
				}
			}

			if (!isLineIconClick && !isLineMenuClick) {
				const lineMenu = document.getElementById('line-menu-popup');
				if (lineMenu) {
					lineMenu.remove();
					isLineMenuOpen = false;
					setTimeout(() => {
						forceBubbleMenuDisplay();
					}, 50);
				}
			}
		};
		
		editorElement.addEventListener('click', handleEditorClick);
		
		const preventDefaultContextMenu = (e: Event) => {
			e.preventDefault();
			return false;
		};
		
		editorElement.addEventListener('contextmenu', preventDefaultContextMenu);
		
		if (editorElement) {
			editorElement.cleanupListeners = () => {
				editorElement?.removeEventListener('click', handleEditorClick);
				editorElement?.removeEventListener('contextmenu', preventDefaultContextMenu);
			};
		}
	}

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

		stopWebsocketCheck();

		document.removeEventListener('click', closeAllDropdowns);
		document.removeEventListener('click', closeLineMenu);
		window.removeEventListener('resize', adjustBubbleMenuPosition);
		
		if (editorElement && editorElement.cleanupListeners) {
			editorElement.cleanupListeners();
		}
		
		const lineMenu = document.getElementById('line-menu-popup');
		if (lineMenu) {
			lineMenu.remove();
		}
	});

	export function getContent() {
		if (!editor) return '';

		return editor.getHTML();
	}

	export function getTitle() {
		return pageTitle;
	}

	
</script>

<TopBar 
	{pageTitle} 
	on:titleChange={handleTitleChange} 
	onNewChat={openSidebar} 
	fileId={getFileId()} 
	token={localStorage.getItem('token') || ""}
	originalFilename={getOriginalFilename()}
/>

<CollaboratorsList users={activeUsers} />

<div class="notion-page-container bg-white dark:bg-gray-900">
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
		background-color: #ffff99;
	}

	:global(.tippy-box[data-theme~='bubble-menu-theme']) {
		background-color: transparent !important;
		box-shadow: none !important;
		transform: translateY(-15px) !important;
		visibility: visible !important;
		display: flex !important;
		z-index: 9999 !important;
	}

	.notion-page-container {
		max-width: 1000px;
		width: 100%;
		margin: 0 auto;
		padding: 2rem 1rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
		color: #2e2e2e;
	}
	
	:global(.dark) .notion-page-container {
		color: #e5e7eb; /* gray-200 */
	}
	
	.editor-wrapper {
		min-height: 500px;
		width: 100%;
		outline: none;
		border: none;
		padding: 0;
		background-color: inherit;
		color: inherit;
		-webkit-touch-callout: none;
		-webkit-user-select: none;
		-khtml-user-select: none;
		-moz-user-select: none;
		-ms-user-select: none;
		user-select: none;
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
	
	:global(.dark) :global(.custom-link) {
		color: #58a6ff;
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

	:global(.ProseMirror) {
		background-color: inherit;
		color: inherit;
		width: 100%;
		padding: 1rem;
		min-height: 70vh;
		cursor: text;
		-webkit-touch-callout: none;
		-webkit-user-select: text;
		-khtml-user-select: text;
		-moz-user-select: text;
		-ms-user-select: text;
		user-select: text;
	}

	:global(.dark) :global(.ProseMirror) {
		color: #e5e7eb;
	}
	
	:global(.dark) :global(.line-highlight) {
		background-color: rgba(255, 255, 0, 0.2);
	}

	:global(.blockquote) {
		border-left: 4px solid #e5e5e5;
		padding-left: 1rem;
		margin-left: 0;
		margin-right: 0;
		font-style: italic;
		color: #666;
	}
	
	:global(.dark) :global(.blockquote) {
		border-left-color: #4a5568;
		color: #a0aec0;
	}

	@media (max-width: 768px) {
		:global(.line-icon) {
			opacity: 0;
			transition: opacity 0.3s;
		}
		:global(.line-icon.visible) {
			opacity: 1;
		}
	}

</style>
