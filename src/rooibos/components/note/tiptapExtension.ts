// tiptapExtension.ts
import StarterKit from '@tiptap/starter-kit';
import Heading from '@tiptap/extension-heading';
import Underline from '@tiptap/extension-underline';
import TextStyle from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import Highlight from '@tiptap/extension-highlight';
import TextAlign from '@tiptap/extension-text-align';
import Link from '@tiptap/extension-link';
import TipTapBubbleMenu from '@tiptap/extension-bubble-menu';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import type { Extension } from '@tiptap/core';
import type { Editor } from '@tiptap/core';

export interface TiptapExtensionOptions {
	bubbleMenuElement: HTMLElement;
	adjustBubbleMenuPosition: () => void;
}

export function getExtensions(options: TiptapExtensionOptions): Extension[] {
	const { bubbleMenuElement, adjustBubbleMenuPosition } = options;

	return [
		StarterKit.configure({
			// 기본 Heading 확장을 비활성화합니다.
			heading: false,
			// 리스트 관련 확장 설정
			bulletList: {
				HTMLAttributes: {
					class: 'bullet-list',
				},
			},
			orderedList: {
				HTMLAttributes: {
					class: 'ordered-list',
				},
			},
			// 코드블록 설정 추가
			codeBlock: {
				HTMLAttributes: {
					class: 'code-block',
				},
			},
			// 인용구 설정 추가
			blockquote: {
				HTMLAttributes: {
					class: 'blockquote',
				},
			},
		}),
		Heading.configure({
			levels: [1, 2, 3, 4, 5, 6]
		}) as unknown as Extension,
		Underline as unknown as Extension,
		TextStyle as unknown as Extension,
		Color,
		Highlight as unknown as Extension,
		TextAlign.configure({
			types: ['heading', 'paragraph']
		}),
		Link.configure({
			openOnClick: true,
			HTMLAttributes: {
				class: 'custom-link',
				target: '_blank',
				rel: 'noopener noreferrer'
			}
		}) as unknown as Extension,
		TaskList.configure({
			HTMLAttributes: {
				class: 'task-list',
			},
		}) as unknown as Extension,
		TaskItem.configure({
			nested: true,
			HTMLAttributes: {
				class: 'task-item',
			},
		}) as unknown as Extension,
		TipTapBubbleMenu.configure({
			element: bubbleMenuElement,
			shouldShow: ({ editor, from, to }: { editor: Editor; from: number; to: number }) => {
				const isVisible = from !== to && editor.isEditable;
				if (isVisible) {
					setTimeout(adjustBubbleMenuPosition, 0);
				}
				return isVisible;
			},
			tippyOptions: {
				duration: 100,
				placement: 'top-start',
				offset: [0, 45],
				theme: 'bubble-menu-theme',
				onShow: () => {
					setTimeout(adjustBubbleMenuPosition, 0);
				}
			}
		}) as unknown as Extension
	];
}
