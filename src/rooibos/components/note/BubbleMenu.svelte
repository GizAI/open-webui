<script>
	// 부모에서 에디터 상태와 각 액션 함수를 props로 전달받습니다.
	export let editorState;
	export let onToggleBold;
	export let onToggleItalic;
	export let onToggleUnderline;
	export let onToggleStrike;
	export let onToggleColorPicker;
	export let onToggleHighlightPicker;
	export let onToggleAlignmentOptions;
	export let onSetLink;
	export let onTranslate;
	export let onRemoveFormat;

	// 포털 컨테이너 관련 props
	export let showColorPicker = false;
	export let showHighlightPicker = false;
	export let showAlignmentOptions = false;
	export let showLinkInput = false;
	export let colorPickerPosition = { x: 0, y: 0 };
	export let highlightPickerPosition = { x: 0, y: 0 };
	export let alignmentDropdownPosition = { x: 0, y: 0 };
	export let linkInputPosition = { x: 0, y: 0 };
	export let linkInputValue = '';
	export let setColor;
	export let setHighlight;
	export let setTextAlignLeft;
	export let setTextAlignCenter;
	export let setTextAlignRight;
	export let applyLink;
	export let handleLinkInputKeydown;

	// 부모와 element 참조를 공유하기 위한 바인딩 변수
	export let menuElement;

	// 취소 버튼 클릭 핸들러
	function cancelLink() {
		showLinkInput = false;
		linkInputValue = '';
	}
</script>

<div
	class="bubble-menu bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-200 border border-transparent dark:border-gray-600"
	bind:this={menuElement}
	style="visibility: hidden; position: absolute; display: inline-flex; align-items: stretch; overflow: hidden; font-size: 14px; line-height: 1.2; border-radius: 8px; box-shadow: rgba(0, 0, 0, 0.1) 0px 14px 28px -6px, rgba(0, 0, 0, 0.06) 0px 2px 4px -1px, rgba(84, 72, 49, 0.08) 0px 0px 0px 1px; pointer-events: auto; padding: 4px; flex-wrap: nowrap; white-space: nowrap;"
>
	<!-- 굵게 -->
	<button
		class="bubble-menu-button text-gray-900 dark:text-gray-200"
		on:click={onToggleBold}
		class:active={editorState.bold}
		title="굵게"
	>
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
				<path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
			</svg>
		</span>
	</button>
	<!-- 기울임 -->
	<button
		class="bubble-menu-button text-gray-900 dark:text-gray-200"
		on:click={onToggleItalic}
		class:active={editorState.italic}
		title="기울임"
	>
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<line x1="19" y1="4" x2="10" y2="4"></line>
				<line x1="14" y1="20" x2="5" y2="20"></line>
				<line x1="15" y1="4" x2="9" y2="20"></line>
			</svg>
		</span>
	</button>
	<!-- 밑줄 -->
	<button
		class="bubble-menu-button text-gray-900 dark:text-gray-200"
		on:click={onToggleUnderline}
		class:active={editorState.underline}
		title="밑줄"
	>
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path>
				<line x1="4" y1="21" x2="20" y2="21"></line>
			</svg>
		</span>
	</button>
	<!-- 취소선 -->
	<button
		class="bubble-menu-button text-gray-900 dark:text-gray-200"
		on:click={onToggleStrike}
		class:active={editorState.strike}
		title="취소선"
	>
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<line x1="5" y1="12" x2="19" y2="12"></line>
				<path d="M16 6C16 6 16.5 8 13 10C11 11.5 10 12 10 14C10 16 12 18 16 18"></path>
			</svg>
		</span>
	</button>
	<!-- 텍스트 색상 -->
	<button
		class="bubble-menu-button text-gray-900 dark:text-gray-200"
		on:click={onToggleColorPicker}
		class:active={editorState.textStyle}
		title="텍스트 색상"
	>
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path
					d="M12 19.5H4.5c-1.5 0-3-1.5-3-3 0-1.5 1.5-3 3-3h3v-3h3v3h3c1.5 0 3 1.5 3 3 0 1.5-1.5 3-3 3H12z"
				/>
				<path d="M16.5 4.5h3v3" />
				<path d="M19.5 4.5l-6 6" />
			</svg>
		</span>
	</button>
	<!-- 하이라이트 -->
	<button
		class="bubble-menu-button text-gray-900 dark:text-gray-200"
		on:click={onToggleHighlightPicker}
		class:active={editorState.highlight}
		title="하이라이트"
	>
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path
					d="M12 2l.642.642L17.5 7.5l-4.5 4.5 5.5 5.5-5.642 5.642L7.5 17.5l4.5-4.5-5.5-5.5L12 2z"
				/>
			</svg>
		</span>
	</button>
	<!-- 텍스트 정렬 -->
	<button class="bubble-menu-button text-gray-900 dark:text-gray-200" on:click={onToggleAlignmentOptions} title="텍스트 정렬">
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<line x1="3" y1="6" x2="21" y2="6"></line>
				<line x1="3" y1="12" x2="21" y2="12"></line>
				<line x1="3" y1="18" x2="21" y2="18"></line>
			</svg>
		</span>
	</button>
	<!-- 링크 추가 -->
	<button
		class="bubble-menu-button text-gray-900 dark:text-gray-200"
		on:click={onSetLink}
		class:active={editorState.link}
		title="링크 추가"
	>
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
				<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
			</svg>
		</span>
	</button>
	<!-- 번역 -->
	<button class="bubble-menu-button text-gray-900 dark:text-gray-200" on:click={onTranslate} title="번역">
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="M5 8l6 6"></path>
				<path d="M4 14h7"></path>
				<path d="M2 5h12"></path>
				<path d="M7 2v3"></path>
				<path d="M22 22l-5-10-5 10"></path>
				<path d="M14 18h6"></path>
			</svg>
		</span>
	</button>
	<!-- 서식 제거 -->
	<button class="bubble-menu-button text-gray-900 dark:text-gray-200" on:click={onRemoveFormat} title="서식 제거">
		<span class="icon">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<line x1="4" y1="4" x2="20" y2="20"></line>
				<line x1="20" y1="4" x2="4" y2="20"></line>
			</svg>
		</span>
	</button>
</div>

<!-- 포털 컨테이너 - noteEditor.svelte에서 이동됨 -->
<div class="portal-container">
	{#if showColorPicker}
		<div
			class="floating-dropdown floating-color-picker bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600"
			style="position: fixed; left: {colorPickerPosition.x}px; top: {colorPickerPosition.y}px;"
		>
			<button
				class="color-option"
				style="background-color: #000000;"
				on:click={() => setColor('#000000')}
			></button>
			<button
				class="color-option"
				style="background-color: #FF0000;"
				on:click={() => setColor('#FF0000')}
			></button>
			<button
				class="color-option"
				style="background-color: #00FF00;"
				on:click={() => setColor('#00FF00')}
			></button>
			<button
				class="color-option"
				style="background-color: #0000FF;"
				on:click={() => setColor('#0000FF')}
			></button>
			<button
				class="color-option"
				style="background-color: #FFFF00;"
				on:click={() => setColor('#FFFF00')}
			></button>
			<button
				class="color-option"
				style="background-color: #FF00FF;"
				on:click={() => setColor('#FF00FF')}
			></button>
			<button
				class="color-option"
				style="background-color: #00FFFF;"
				on:click={() => setColor('#00FFFF')}
			></button>
		</div>
	{/if}

	{#if showHighlightPicker}
		<div
			class="floating-dropdown floating-color-picker bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600"
			style="position: fixed; left: {highlightPickerPosition.x}px; top: {highlightPickerPosition.y}px;"
		>
			<button
				class="color-option"
				style="background-color: #FFFF00;"
				on:click={() => setHighlight('#FFFF00')}
			></button>
			<button
				class="color-option"
				style="background-color: #FFA500;"
				on:click={() => setHighlight('#FFA500')}
			></button>
			<button
				class="color-option"
				style="background-color: #FF69B4;"
				on:click={() => setHighlight('#FF69B4')}
			></button>
			<button
				class="color-option"
				style="background-color: #7FFFD4;"
				on:click={() => setHighlight('#7FFFD4')}
			></button>
			<button
				class="color-option"
				style="background-color: #90EE90;"
				on:click={() => setHighlight('#90EE90')}
			></button>
		</div>
	{/if}

	{#if showAlignmentOptions}
		<div
			class="floating-dropdown floating-alignment-dropdown bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600"
			style="position: fixed; left: {alignmentDropdownPosition.x}px; top: {alignmentDropdownPosition.y}px;"
		>
			<button
				class="alignment-option text-gray-900 dark:text-gray-200"
				on:click={setTextAlignLeft}
				class:active={editorState.textAlignLeft}
				title="왼쪽 정렬"
			>
				<span class="icon">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<line x1="3" y1="6" x2="21" y2="6"></line>
						<line x1="3" y1="12" x2="15" y2="12"></line>
						<line x1="3" y1="18" x2="18" y2="18"></line>
					</svg>
				</span>
			</button>
			<button
				class="alignment-option text-gray-900 dark:text-gray-200"
				on:click={setTextAlignCenter}
				class:active={editorState.textAlignCenter}
				title="가운데 정렬"
			>
				<span class="icon">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<line x1="3" y1="6" x2="21" y2="6"></line>
						<line x1="6" y1="12" x2="18" y2="12"></line>
						<line x1="3" y1="18" x2="21" y2="18"></line>
					</svg>
				</span>
			</button>
			<button
				class="alignment-option text-gray-900 dark:text-gray-200"
				on:click={setTextAlignRight}
				class:active={editorState.textAlignRight}
				title="오른쪽 정렬"
			>
				<span class="icon">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<line x1="3" y1="6" x2="21" y2="6"></line>
						<line x1="9" y1="12" x2="21" y2="12"></line>
						<line x1="6" y1="18" x2="21" y2="18"></line>
					</svg>
				</span>
			</button>
		</div>
	{/if}

	{#if showLinkInput}
		<div
			class="floating-dropdown floating-link-input bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600"
			style="position: fixed; left: {linkInputPosition.x}px; top: {linkInputPosition.y}px;"
		>
			<div class="link-input-container">
				<div class="link-input-row">
					<input
						id="link-input"
						type="text"
						bind:value={linkInputValue}
						placeholder="URL 입력"
						on:keydown={handleLinkInputKeydown}
						autofocus
						class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-200 border border-gray-200 dark:border-gray-600"
					/>
					<button class="link-button text-gray-900 dark:text-gray-200 border border-gray-200 dark:border-gray-600" on:click={applyLink}>적용</button>
					<button class="link-button cancel-button text-gray-900 dark:text-gray-200 border border-gray-200 dark:border-gray-600" on:click={cancelLink}>취소</button>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
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
	
	:global(.dark) .bubble-menu::-webkit-scrollbar-thumb {
		background-color: rgba(255, 255, 255, 0.2);
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
	
	:global(.dark) .bubble-menu-button {
		color: #e5e7eb;
	}
	
	:global(.dark) .bubble-menu-button:hover {
		background-color: rgba(255, 255, 255, 0.1);
	}
	
	:global(.dark) .bubble-menu-button.active {
		background-color: rgba(255, 255, 255, 0.2);
		color: #fff;
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

	/* 포털 컨테이너 관련 스타일 - noteEditor.svelte에서 이동됨 */
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

	.floating-dropdown {
		position: fixed !important;
		display: flex;
		border-radius: 4px;
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
		padding: 4px;
		z-index: 9999 !important;
		pointer-events: auto;
	}
	
	:global(.dark) .floating-dropdown {
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
	}

	.floating-color-picker {
		flex-wrap: wrap;
		width: 120px;
	}

	.floating-alignment-dropdown {
		flex-direction: column;
		width: 40px;
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
		border-radius: 4px;
		font-size: 14px;
		margin-right: 4px;
	}

	.link-button {
		padding: 6px 10px;
		background-color: #f5f5f5;
		border-radius: 4px;
		cursor: pointer;
		font-size: 12px;
		white-space: nowrap;
	}
	
	:global(.dark) .link-button {
		background-color: #374151;
	}

	.link-button:hover {
		background-color: #e5e5e5;
	}
	
	:global(.dark) .link-button:hover {
		background-color: #4B5563;
	}

	.color-option {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		border: 1px solid #ddd;
		margin: 2px;
		cursor: pointer;
	}
	
	:global(.dark) .color-option {
		border-color: #4B5563;
	}

	.color-option:hover {
		transform: scale(1.1);
	}

	.alignment-option {
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
		margin: 2px;
		transition: background-color 0.2s ease;
	}

	.alignment-option:hover {
		background-color: rgba(0, 0, 0, 0.05);
	}
	
	:global(.dark) .alignment-option:hover {
		background-color: rgba(255, 255, 255, 0.1);
	}

	.alignment-option.active {
		background-color: rgba(0, 0, 0, 0.1);
		color: #000;
	}
	
	:global(.dark) .alignment-option.active {
		background-color: rgba(255, 255, 255, 0.2);
		color: #fff;
	}

	.cancel-button {
		margin-left: 4px;
		background-color: #f8f8f8;
	}
	
	:global(.dark) .cancel-button {
		background-color: #374151;
	}

	.cancel-button:hover {
		background-color: #e0e0e0;
	}
	
	:global(.dark) .cancel-button:hover {
		background-color: #4B5563;
	}
	
	:global(.bubble-menu) {
		/* 기존 인라인 스타일을 덮어쓰려면 !important 사용 */
		padding: 8px !important;
		font-size: 16px !important;
	}
	:global(.bubble-menu-button) {
		width: 36px !important;
		height: 36px !important;
	}
	:global(.icon svg) {
		width: 20px !important;
		height: 20px !important;
		stroke-width: 3 !important; /* 굵은 효과 */
	}
</style>
