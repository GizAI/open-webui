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

  // 부모와 element 참조를 공유하기 위한 바인딩 변수
  export let menuElement;
</script>

<div 
  class="bubble-menu"
  bind:this={menuElement}
  style="visibility: hidden; position: absolute; display: inline-flex; align-items: stretch; background: white; overflow: hidden; font-size: 14px; line-height: 1.2; border-radius: 8px; box-shadow: rgba(0, 0, 0, 0.1) 0px 14px 28px -6px, rgba(0, 0, 0, 0.06) 0px 2px 4px -1px, rgba(84, 72, 49, 0.08) 0px 0px 0px 1px; pointer-events: auto; padding: 4px; flex-wrap: nowrap; white-space: nowrap;"
>
  <!-- 굵게 -->
  <button
    class="bubble-menu-button"
    on:click={onToggleBold}
    class:active={editorState.bold}
    title="굵게"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
        <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
      </svg>
    </span>
  </button>
  <!-- 기울임 -->
  <button
    class="bubble-menu-button"
    on:click={onToggleItalic}
    class:active={editorState.italic}
    title="기울임"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="19" y1="4" x2="10" y2="4"></line>
        <line x1="14" y1="20" x2="5" y2="20"></line>
        <line x1="15" y1="4" x2="9" y2="20"></line>
      </svg>
    </span>
  </button>
  <!-- 밑줄 -->
  <button
    class="bubble-menu-button"
    on:click={onToggleUnderline}
    class:active={editorState.underline}
    title="밑줄"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path>
        <line x1="4" y1="21" x2="20" y2="21"></line>
      </svg>
    </span>
  </button>
  <!-- 취소선 -->
  <button
    class="bubble-menu-button"
    on:click={onToggleStrike}
    class:active={editorState.strike}
    title="취소선"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="5" y1="12" x2="19" y2="12"></line>
        <path d="M16 6C16 6 16.5 8 13 10C11 11.5 10 12 10 14C10 16 12 18 16 18"></path>
      </svg>
    </span>
  </button>
  <!-- 텍스트 색상 -->
  <button
    class="bubble-menu-button"
    on:click={onToggleColorPicker}
    class:active={editorState.textStyle}
    title="텍스트 색상"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 19.5H4.5c-1.5 0-3-1.5-3-3 0-1.5 1.5-3 3-3h3v-3h3v3h3c1.5 0 3 1.5 3 3 0 1.5-1.5 3-3 3H12z"/>
        <path d="M16.5 4.5h3v3"/>
        <path d="M19.5 4.5l-6 6"/>
      </svg>
    </span>
  </button>
  <!-- 하이라이트 -->
  <button
    class="bubble-menu-button"
    on:click={onToggleHighlightPicker}
    class:active={editorState.highlight}
    title="하이라이트"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2l.642.642L17.5 7.5l-4.5 4.5 5.5 5.5-5.642 5.642L7.5 17.5l4.5-4.5-5.5-5.5L12 2z"/>
      </svg>
    </span>
  </button>
  <!-- 텍스트 정렬 -->
  <button
    class="bubble-menu-button"
    on:click={onToggleAlignmentOptions}
    title="텍스트 정렬"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
      </svg>
    </span>
  </button>
  <!-- 링크 추가 -->
  <button
    class="bubble-menu-button"
    on:click={onSetLink}
    class:active={editorState.link}
    title="링크 추가"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
      </svg>
    </span>
  </button>
  <!-- 번역 -->
  <button
    class="bubble-menu-button"
    on:click={onTranslate}
    title="번역"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
  <button
    class="bubble-menu-button"
    on:click={onRemoveFormat}
    title="서식 제거"
  >
    <span class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="4" x2="20" y2="20"></line>
        <line x1="20" y1="4" x2="4" y2="20"></line>
      </svg>
    </span>
  </button>
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
  .icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .icon svg {
    width: 14px;
    height: 14px;
  }
</style>
