<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function closeSidebar() {
    dispatch('close');
  }
</script>

<div class="sidebar">
  <button class="close-btn" on:click={closeSidebar}>닫기</button>
  <div class="content">
    <!-- 사이드바 내부 콘텐츠를 여기에 작성 -->
    <p>여기는 새채팅 사이드바 입니다.</p>
  </div>
</div>

<style>
  .sidebar {
    position: fixed;
    top: 0;
    right: 0;
    width: 300px;
    height: 100%;
    background-color: #f9f9f9;
    box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
    padding: 1rem;
    z-index: 1000;
  }
  .close-btn {
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    margin-bottom: 1rem;
  }
</style>
