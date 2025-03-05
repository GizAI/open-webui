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

	/* [추가] ProseMirror 데코레이션을 위한 import */
	import { Extension } from '@tiptap/core';
	import { Plugin, PluginKey } from 'prosemirror-state';
	import { Decoration, DecorationSet } from 'prosemirror-view';

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

	function initCollaboration() {
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
									
									// 위젯 데코레이션으로 아이콘 삽입
									const deco = Decoration.widget(
										pos,
										() => {
											const icon = document.createElement('div');
											icon.className = 'line-icon';
											
											// 세로로 배치된 점 3개 생성
											for (let i = 0; i < 3; i++) {
												const dot = document.createElement('div');
												dot.className = 'line-icon-dot';
												icon.appendChild(dot);
											}
											
											// 아이콘 스타일 직접 적용
											icon.style.cursor = 'pointer';
											icon.style.userSelect = 'none';
											icon.style.display = 'flex';
											icon.style.flexDirection = 'column';
											icon.style.gap = '2px';
											icon.style.alignItems = 'center';
											icon.style.justifyContent = 'center';
											icon.style.padding = '4px';
											icon.style.position = 'absolute';
											icon.style.left = '-24px';
											icon.style.top = '50%';
											icon.style.transform = 'translateY(-50%)';
											icon.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
											icon.style.borderRadius = '4px';
											icon.style.zIndex = '10';
											icon.style.width = '18px';
											icon.style.height = '18px';
											icon.style.opacity = '0';
											icon.style.transition = 'opacity 0.2s';
											
											// 부모 요소에 마우스 오버 이벤트 추가
											const handleParentHover = () => {
												icon.style.opacity = '1';
											};
											
											const handleParentLeave = () => {
												if (!icon.matches(':hover')) {
													icon.style.opacity = '0';
												}
											};
											
											// 아이콘 자체에 마우스 오버 이벤트 추가
											icon.addEventListener('mouseover', () => {
												icon.style.backgroundColor = 'rgba(0, 0, 0, 0.1)';
												icon.style.opacity = '1';
											});
											
											icon.addEventListener('mouseout', () => {
												icon.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
												if (!document.querySelector('.line-block:hover')) {
													icon.style.opacity = '0';
												}
											});
											
											// 클릭 이벤트
											icon.addEventListener('click', (e) => {
												e.preventDefault();
												e.stopPropagation();
												
												// 아이콘 클릭 시 메뉴 표시
												showLineMenu(
													e.clientX,
													e.clientY,
													() => {
														// 굵게
														extensionThis.editor
															.chain()
															.focus()
															.setTextSelection({ from: pos + 1, to: pos + node.nodeSize - 1 })
															.toggleBold()
															.run();
													},
													() => {
														// 이탤릭
														extensionThis.editor
															.chain()
															.focus()
															.setTextSelection({ from: pos + 1, to: pos + node.nodeSize - 1 })
															.toggleItalic()
															.run();
													},
													pos,
													node
												);
											});
											
											// 아이콘이 생성된 후 부모 요소에 이벤트 리스너 추가
											setTimeout(() => {
												const parentBlock = icon.closest('.line-block') || 
													document.querySelector(`.line-block[data-node-id="${pos}"]`) ||
													icon.parentElement;
												
												if (parentBlock) {
													parentBlock.addEventListener('mouseover', handleParentHover);
													parentBlock.addEventListener('mouseout', handleParentLeave);
													
													// 클린업 함수 설정
													icon.cleanupListeners = () => {
														parentBlock.removeEventListener('mouseover', handleParentHover);
														parentBlock.removeEventListener('mouseout', handleParentLeave);
													};
												}
											}, 0);
											
											return icon;
										},
										{ side: -1 }
									);
									decorations.push(deco);
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

	/* [추가] showLineMenu 함수를 확장하여 노션처럼 "Paragraph / Heading1~3 / Bullet / Ordered / Ask AI" 메뉴 추가 */
	function showLineMenu(x, y, onBold, onItalic, pos, node) {
		const oldMenu = document.getElementById('line-menu-popup');
		if (oldMenu) {
			oldMenu.remove();
		}

		const menu = document.createElement('div');
		menu.id = 'line-menu-popup';
		menu.style.position = 'absolute';
		menu.style.left = x + 'px';
		menu.style.top = y + 'px';
		menu.style.transform = 'translateX(-100%)';
		menu.style.padding = '8px';
		menu.style.border = '1px solid #eee';
		menu.style.background = '#fff';
		menu.style.zIndex = '9999';
		menu.style.borderRadius = '6px';
		menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
		menu.style.display = 'flex';
		menu.style.flexDirection = 'column';
		menu.style.gap = '4px';
		menu.style.minWidth = '180px';
		menu.style.maxWidth = '220px';
		menu.style.fontSize = '14px';

		// 메뉴 항목 스타일 함수
		const styleMenuItem = (btn, icon) => {
			btn.style.display = 'flex';
			btn.style.alignItems = 'center';
			btn.style.gap = '8px';
			btn.style.padding = '6px 8px';
			btn.style.border = 'none';
			btn.style.borderRadius = '4px';
			btn.style.background = 'transparent';
			btn.style.cursor = 'pointer';
			btn.style.width = '100%';
			btn.style.textAlign = 'left';
			btn.style.fontSize = '14px';
			btn.style.color = '#333';
			
			if (icon) {
				const iconSpan = document.createElement('span');
				iconSpan.innerHTML = icon;
				iconSpan.style.display = 'inline-flex';
				iconSpan.style.width = '20px';
				iconSpan.style.height = '20px';
				iconSpan.style.alignItems = 'center';
				iconSpan.style.justifyContent = 'center';
				btn.prepend(iconSpan);
			}
			
			btn.onmouseover = () => {
				btn.style.background = '#f5f5f5';
			};
			btn.onmouseout = () => {
				btn.style.background = 'transparent';
			};
		};

		// 구분선 추가 함수
		const addDivider = () => {
			const divider = document.createElement('div');
			divider.style.height = '1px';
			divider.style.background = '#eee';
			divider.style.margin = '4px 0';
			menu.appendChild(divider);
		};

		// 블록 변환 섹션
		const blockHeader = document.createElement('div');
		blockHeader.style.fontSize = '12px';
		blockHeader.style.color = '#888';
		blockHeader.style.padding = '4px 8px';
		menu.appendChild(blockHeader);

		const extensionEditor = editor; // 전역 editor 참조(또는 extensionThis.editor 참조)
		const fromPos = pos + 1;
		const toPos = pos + node.nodeSize - 1;

		// 현재 노드 타입 확인 함수
		const isNodeType = (type, attrs = {}) => {
			if (!extensionEditor || !node) return false;
			
			if (type === 'paragraph') {
				return node.type.name === 'paragraph';
			} else if (type === 'heading') {
				return node.type.name === 'heading' && node.attrs.level === attrs.level;
			} else if (type === 'bulletList') {
				return node.type.name === 'bulletList' || 
					(node.type.name === 'listItem' && node.parent?.type.name === 'bulletList');
			} else if (type === 'orderedList') {
				return node.type.name === 'orderedList' || 
					(node.type.name === 'listItem' && node.parent?.type.name === 'orderedList');
			}
			return false;
		};

		// 메뉴 항목 활성화 함수
		const styleActiveMenuItem = (btn, isActive) => {
			if (isActive) {
				btn.style.background = '#f0f0f0';
				btn.style.fontWeight = 'bold';
				
				// 체크 아이콘 추가
				const checkIcon = document.createElement('span');
				checkIcon.innerHTML = '✓';
				checkIcon.style.marginLeft = 'auto';
				checkIcon.style.color = '#4caf50';
				btn.appendChild(checkIcon);
			}
		};

		// Paragraph
		const paragraphBtn = document.createElement('button');
		paragraphBtn.textContent = 'Paragraph';
		styleMenuItem(paragraphBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 6v12M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
		styleActiveMenuItem(paragraphBtn, isNodeType('paragraph'));
		paragraphBtn.onclick = () => {
			extensionEditor
				.chain()
				.focus()
				.setTextSelection({ from: fromPos, to: toPos })
				.setNode('paragraph')
				.run();
			closeMenu();
		};
		menu.appendChild(paragraphBtn);

		// Heading 1
		const heading1Btn = document.createElement('button');
		heading1Btn.textContent = 'Heading 1';
		styleMenuItem(heading1Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
		styleActiveMenuItem(heading1Btn, isNodeType('heading', { level: 1 }));
		heading1Btn.onclick = () => {
			extensionEditor
				.chain()
				.focus()
				.setTextSelection({ from: fromPos, to: toPos })
				.setNode('heading', { level: 1 })
				.run();
			closeMenu();
		};
		menu.appendChild(heading1Btn);

		// Heading 2
		const heading2Btn = document.createElement('button');
		heading2Btn.textContent = 'Heading 2';
		styleMenuItem(heading2Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
		styleActiveMenuItem(heading2Btn, isNodeType('heading', { level: 2 }));
		heading2Btn.onclick = () => {
			extensionEditor
				.chain()
				.focus()
				.setTextSelection({ from: fromPos, to: toPos })
				.setNode('heading', { level: 2 })
				.run();
			closeMenu();
		};
		menu.appendChild(heading2Btn);

		// Heading 3
		const heading3Btn = document.createElement('button');
		heading3Btn.textContent = 'Heading 3';
		styleMenuItem(heading3Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
		styleActiveMenuItem(heading3Btn, isNodeType('heading', { level: 3 }));
		heading3Btn.onclick = () => {
			extensionEditor
				.chain()
				.focus()
				.setTextSelection({ from: fromPos, to: toPos })
				.setNode('heading', { level: 3 })
				.run();
			closeMenu();
		};
		menu.appendChild(heading3Btn);

		// 리스트 섹션 위에 구분선 추가
		addDivider();

		// Bullet list
		const bulletBtn = document.createElement('button');
		bulletBtn.textContent = 'Bullet list';
		styleMenuItem(bulletBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
		styleActiveMenuItem(bulletBtn, isNodeType('bulletList'));
		bulletBtn.onclick = () => {
			extensionEditor
				.chain()
				.focus()
				.setTextSelection({ from: fromPos, to: toPos })
				.toggleBulletList()
				.run();
			closeMenu();
		};
		menu.appendChild(bulletBtn);

		// Ordered list
		const orderedBtn = document.createElement('button');
		orderedBtn.textContent = 'Ordered list';
		styleMenuItem(orderedBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 6h11M10 12h11M10 18h11M4 6h1v4M4 10h2M4 18h3M4 14h2v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
		styleActiveMenuItem(orderedBtn, isNodeType('orderedList'));
		orderedBtn.onclick = () => {
			extensionEditor
				.chain()
				.focus()
				.setTextSelection({ from: fromPos, to: toPos })
				.toggleOrderedList()
				.run();
			closeMenu();
		};
		menu.appendChild(orderedBtn);

		addDivider();

		// AI 섹션
		// Ask AI
		const askAI = document.createElement('button');
		askAI.textContent = 'Ask AI';
		styleMenuItem(askAI, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2a10 10 0 1 0 10 10 10 10 0 0 0-10-10zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8zm0-13a1 1 0 0 0-1 1v5a1 1 0 0 0 2 0V8a1 1 0 0 0-1-1zm0 10a1.5 1.5 0 1 0-1.5-1.5A1.5 1.5 0 0 0 12 17z" fill="currentColor"/></svg>');
		askAI.onclick = () => {
			closeMenu();
			openSidebar(); // 기존 함수 사용
		};
		menu.appendChild(askAI);

		document.body.appendChild(menu);

		function handleClickOutside(e) {
			if (!menu.contains(e.target)) {
				closeMenu();
			}
		}
		document.addEventListener('mousedown', handleClickOutside);

		function closeMenu() {
			menu.remove();
			document.removeEventListener('mousedown', handleClickOutside);
		}
	}

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
				LineMenuExtension // [추가] 우리가 만든 라인 메뉴 확장
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
		if (note) {
			pageTitle = note.title || '새 페이지';
		} else {
			pageTitle = '새 페이지';
		}

		provider = initCollaboration();

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
