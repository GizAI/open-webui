// tiptapExtension.ts
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import TextStyle from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import Highlight from '@tiptap/extension-highlight';
import TextAlign from '@tiptap/extension-text-align';
import Link from '@tiptap/extension-link';
import TipTapBubbleMenu from '@tiptap/extension-bubble-menu';
import type { Extension } from '@tiptap/core';

export interface TiptapExtensionOptions {
	bubbleMenuElement: HTMLElement;
	adjustBubbleMenuPosition: () => void;
}

/**
 * NoteEditor에서 사용할 tiptap 확장(extension)들을 반환합니다.
 *
 * @param options - bubbleMenuElement와 adjustBubbleMenuPosition 함수를 포함하는 옵션 객체
 * @returns Extension[] 배열
 */
export function getExtensions(options: TiptapExtensionOptions): Extension[] {
	const { bubbleMenuElement, adjustBubbleMenuPosition } = options;

	return [
		StarterKit,
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
				rel: 'noopener noreferrer',
				contenteditable: 'false'
			}
		}) as unknown as Extension,
		TipTapBubbleMenu.configure({
			element: bubbleMenuElement,
			shouldShow: ({ editor, from, to }: { editor: any; from: number; to: number }) => {
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
