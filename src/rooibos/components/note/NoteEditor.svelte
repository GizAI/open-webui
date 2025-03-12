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

	// Initialize the event dispatcher
	const dispatch = createEventDispatcher();

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

	// 파일 ID 확인
	function getFileId(): string {
		if (!selectedFile) return "";
		return selectedFile.id || "";
	}

	// 파일명 확인
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

	let provider: HocuspocusProvider | null = null;
	let activeUsers: ActiveUser[] = [];

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
			textAlignRight: editor.isActive({ textAlign: 'right' }),
			heading3: editor.isActive('heading', { level: 3 })
		};
	}

	/**
	 * Forces the bubble menu to display if conditions are met
	 */
	 function forceBubbleMenuDisplay(): void {
		if (!bubbleMenuElement || !editor || isLineMenuOpen) return;
		// 버블 메뉴는 TextSelection일 때만 나타나야 함
		if (!(editor.state.selection instanceof TextSelection) || editor.state.selection.empty) return;
		
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
	
		// 라인 메뉴도 닫기
		const lineMenu = document.getElementById('line-menu-popup');
		if (lineMenu) {
			lineMenu.remove();
			isLineMenuOpen = false;
		}
	
		if (editor) {
			editor.view.dispatch(editor.state.tr.setMeta('toggleLineHighlight', null));
		}
	}

	// 문서 전체 클릭 시 라인 메뉴 닫기 함수
	function closeLineMenu(e: MouseEvent): void {
		// 라인 아이콘이나 라인 메뉴 내부 클릭이 아닌 경우에만 처리
		if (!e.target) return;
		
		const target = e.target as HTMLElement;
		const isLineIconClick = target.closest('.line-icon') !== null;
		const isLineMenuClick = target.closest('#line-menu-popup') !== null;
		
		if (!isLineIconClick && !isLineMenuClick) {
			const lineMenu = document.getElementById('line-menu-popup');
			if (lineMenu) {
				lineMenu.remove();
				isLineMenuOpen = false;
				
				// 라인 메뉴가 닫힐 때 버블 메뉴 상태 업데이트
				setTimeout(() => {
					forceBubbleMenuDisplay();
				}, 50);
			}
		}
	}

	function handleTitleChange(e: CustomEvent<string>): void {
		pageTitle = e.detail;
		manualTitleEdited = true;
		
		// selectedFile 객체의 파일명도 업데이트
		if (selectedFile) {
			// 파일명 업데이트 (확장자 제외)
			if (selectedFile.name) {
				selectedFile.name = pageTitle;
			}
			if (selectedFile.filename) {
				// 확장자 유지
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

	function setupCollaboration(): HocuspocusProvider {
		const documentName = `note:${noteId}`;
		const currentUser = get(user);

		const token = localStorage.getItem('token') || '';
		
		console.log('Setting up collaboration with:', {
			url: window.location.hostname === 'localhost'
				? 'ws://localhost:8444'
				: 'wss://hocuspocus.conting.ai/ws',
			documentName,
			token: token ? 'Token exists (not shown)' : 'No token',
			userId: currentUser?.id || 'Unknown'
		});

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

		setInterval(() => {
			if (providerInstance.websocket) {
				const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
				console.log('WebSocket status:', states[providerInstance.websocket.readyState]);
				
				if (providerInstance.websocket.readyState === WebSocket.CLOSED) {
					console.log('WebSocket is closed. Attempting to reconnect...');
					providerInstance.connect();
				}
			} else {
				console.log('WebSocket not initialized');
			}
		}, 10000);

		const yActiveUsers = providerInstance.document.getMap('activeUsers');
		yActiveUsers.observe(() => {
			activeUsers = Array.from(yActiveUsers.values()) as ActiveUser[];
		});

		return providerInstance;
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
									// taskItem 노드에 대해서는 라인 아이콘을 생성하지 않음
									if (node.type.name === 'taskItem') {
										return true;
									}
									
									const classes = ['line-block'];
									if (highlightedPos === pos) {
										classes.push('line-highlight');
									}
									const blockDeco = Decoration.node(pos, pos + node.nodeSize, {
										class: classes.join(' ')
									});
									decorations.push(blockDeco);
				
									const lineIcon = document.createElement('div');
									lineIcon.className = 'line-icon';
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
											
											// 이미 라인 메뉴가 열려있는 경우 닫기
											const existingMenu = document.getElementById('line-menu-popup');
											if (existingMenu) {
												existingMenu.remove();
												isLineMenuOpen = false;
											}
											
											// 같은 라인의 메뉴가 이미 열려있는 경우 닫고 종료
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
			content: typeof content === 'string' ? content : '',
			autofocus: true,
			onSelectionUpdate({ editor }) {
				setTimeout(() => {
					updateEditorState();
				}, 0);
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
					console.error('노트 content 파싱 오류:', e);
					console.log('Treating content as plain text/HTML');
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
		
		// 문서 전체 클릭 이벤트 리스너 추가
		document.addEventListener('click', closeLineMenu);
		
		// 에디터 영역 클릭 시 라인 메뉴 닫기
		if (editorElement) {
			const handleEditorClick = (e: MouseEvent) => {
				// 라인 아이콘 클릭이나 라인 메뉴 클릭이 아닌 경우에만 처리
				if (!e.target) return;
				
				const target = e.target as HTMLElement;
				const isLineIconClick = target.closest('.line-icon') !== null;
				const isLineMenuClick = target.closest('#line-menu-popup') !== null;
				
				if (!isLineIconClick && !isLineMenuClick) {
					const lineMenu = document.getElementById('line-menu-popup');
					if (lineMenu) {
						lineMenu.remove();
						isLineMenuOpen = false;
						
						// 라인 메뉴가 닫힐 때 버블 메뉴 상태 업데이트
						setTimeout(() => {
							forceBubbleMenuDisplay();
						}, 50);
					}
				}
			};
			
			editorElement.addEventListener('click', handleEditorClick);
			
			// 이벤트 리스너 정리 함수 설정
			if (editorElement) {
				editorElement.cleanupListeners = () => {
					editorElement?.removeEventListener('click', handleEditorClick);
				};
			}
		}

		// 에디터 초기화 후 상태 업데이트
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
		document.removeEventListener('click', closeLineMenu);
		window.removeEventListener('resize', adjustBubbleMenuPosition);
		
		// 에디터 클릭 이벤트 리스너 제거
		if (editorElement && editorElement.cleanupListeners) {
			editorElement.cleanupListeners();
		}
		
		// 라인 메뉴가 열려있으면 닫기
		const lineMenu = document.getElementById('line-menu-popup');
		if (lineMenu) {
			lineMenu.remove();
		}
	});

	export function getContent() {
		if (!editor) return '';
		// 에디터 내용을 문자열 또는 필요한 형식으로 반환
		return editor.getHTML(); // 또는 다른 적절한 메서드
	}

	export function getTitle() {
		// 페이지 제목 반환
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
	
	:global(.dark) .notion-page-container {
		color: #e5e7eb; /* gray-200 */
	}
	
	.editor-wrapper {
		min-height: 400px;
		outline: none;
		border: none;
		padding: 0;
		background-color: inherit;
		color: inherit;
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
	}

	:global(.dark) :global(.ProseMirror) {
		color: #e5e7eb;
	}
	
	:global(.dark) :global(.line-highlight) {
		background-color: rgba(255, 255, 0, 0.2); /* 다크모드에서 하이라이트 색상 조정 */
	}
</style>
