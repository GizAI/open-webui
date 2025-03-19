<script context="module">
  function isNodeType(editor, node, type, attrs = {}) {
    if (!editor || !node) return false;
    
    if (type === 'paragraph') {
      return node.type.name === 'paragraph';
    } else if (type === 'heading') {
      return node.type.name === 'heading' && node.attrs.level === attrs.level;
    } else if (type === 'bulletList') {
      return node.type.name === 'bulletList';
    } else if (type === 'orderedList') {
      return node.type.name === 'orderedList';
    } else if (type === 'taskList') {
      return node.type.name === 'taskList';
    } else if (type === 'codeBlock') {
      return node.type.name === 'codeBlock';
    } else if (type === 'blockquote') {
      return node.type.name === 'blockquote';
    }
    return false;
  }

  function styleMenuItem(btn, icon) {
    btn.style.display = 'flex';
    btn.style.alignItems = 'center';
    btn.style.gap = '4px';
    btn.style.padding = '6px 8px';
    btn.style.border = 'none';
    btn.style.borderRadius = '4px';
    btn.style.background = 'transparent';
    btn.style.cursor = 'pointer';
    btn.style.width = '100%';
    btn.style.textAlign = 'left';
    btn.style.fontSize = '14px';
    btn.style.color = '#333';
    
    const isDarkMode = document.documentElement.classList.contains('dark');
    if (isDarkMode) {
      btn.style.color = '#e5e7eb';
    }
    
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
      btn.style.background = isDarkMode ? '#374151' : '#f5f5f5';
    };
    btn.onmouseout = () => {
      btn.style.background = 'transparent';
    };
  }

  function styleActiveMenuItem(btn, isActive) {
    const isDarkMode = document.documentElement.classList.contains('dark');
    
    if (isActive) {
      btn.style.background = isDarkMode ? '#4B5563' : '#f0f0f0';
      btn.style.fontWeight = 'bold';
      
      const checkIcon = document.createElement('span');
      checkIcon.innerHTML = '✓';
      checkIcon.style.marginLeft = 'auto';
      checkIcon.style.color = '#4caf50';
      btn.appendChild(checkIcon);
    }
  }

  function addDivider(menu) {
    const divider = document.createElement('div');
    divider.style.height = '1px';
    const isDarkMode = document.documentElement.classList.contains('dark');
    divider.style.background = isDarkMode ? '#4B5563' : '#eee';
    divider.style.margin = '4px 0';
    menu.appendChild(divider);
  }

  let currentOpenMenu = null;
  let currentClickOutsideHandler = null;

  export function showLineMenu(x, y, editor, node, pos, openSidebarCallback) {
    if (currentOpenMenu) {
      currentOpenMenu.remove();
      if (currentClickOutsideHandler) {
        document.removeEventListener('mousedown', currentClickOutsideHandler);
        currentClickOutsideHandler = null;
      }
    }
    
    const isDarkMode = document.documentElement.classList.contains('dark');
    
    const menu = document.createElement('div');
    menu.id = 'line-menu-popup';
    menu.style.position = 'absolute';
    menu.style.left = (x + 30) + 'px';
    menu.style.top = y + 'px';
    menu.style.transform = 'translateY(10px)';
    menu.style.padding = '8px';
    menu.style.border = '1px solid #eee';
    menu.style.background = '#fff';
    menu.style.color = '#333';
    menu.style.zIndex = '9999';
    menu.style.borderRadius = '6px';
    menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    
    if (isDarkMode) {
      menu.style.border = '1px solid #4B5563';
      menu.style.background = '#111827';
      menu.style.color = '#e5e7eb';
      menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
    }
    
    menu.style.display = 'flex';
    menu.style.flexDirection = 'column';
    menu.style.gap = '4px';
    menu.style.minWidth = '180px';
    menu.style.maxWidth = '220px';
    menu.style.fontSize = '14px';
    
    
    const paragraphBtn = document.createElement('button');
    paragraphBtn.textContent = '본문';
    styleMenuItem(paragraphBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><text x="8" y="17" font-size="16" font-weight="bold" fill="currentColor">P</text></svg>');
    styleActiveMenuItem(paragraphBtn, isNodeType(editor, node, 'paragraph'));
    paragraphBtn.onclick = () => {
      try {
        editor.chain().focus().setNode('paragraph').run();
      } catch (error) {
        console.error('본문 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(paragraphBtn);
    
    const heading1Btn = document.createElement('button');
    heading1Btn.textContent = '제목1';
    styleMenuItem(heading1Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(heading1Btn, isNodeType(editor, node, 'heading', { level: 1 }));
    heading1Btn.onclick = () => {
      try {
        if (editor.isActive('heading', { level: 1 })) {
          editor.chain().focus().setNode('paragraph').run();
        } else {
          editor.chain().focus().setNode('heading', { level: 1 }).run();
        }
      } catch (error) {
        console.error('제목1 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(heading1Btn);
    
    const heading2Btn = document.createElement('button');
    heading2Btn.textContent = '제목2';
    styleMenuItem(heading2Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(heading2Btn, isNodeType(editor, node, 'heading', { level: 2 }));
    heading2Btn.onclick = () => {
      try {
        if (editor.isActive('heading', { level: 2 })) {
          editor.chain().focus().setNode('paragraph').run();
        } else {
          editor.chain().focus().setNode('heading', { level: 2 }).run();
        }
      } catch (error) {
        console.error('제목2 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(heading2Btn);
    
    const heading3Btn = document.createElement('button');
    heading3Btn.textContent = '제목3';
    styleMenuItem(heading3Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(heading3Btn, isNodeType(editor, node, 'heading', { level: 3 }));
    heading3Btn.onclick = () => {
      try {
        if (editor.isActive('heading', { level: 3 })) {
          editor.chain().focus().setNode('paragraph').run();
        } else {
          editor.chain().focus().setNode('heading', { level: 3 }).run();
        }
      } catch (error) {
        console.error('제목3 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(heading3Btn);
    
    addDivider(menu);
    
    const bulletBtn = document.createElement('button');
    bulletBtn.textContent = '글머리 기호';
    styleMenuItem(bulletBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(bulletBtn, isNodeType(editor, node, 'bulletList'));
    bulletBtn.onclick = () => {
      try {
        editor.chain().focus().toggleBulletList().run();
      } catch (error) {
        console.error('글머리 기호 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(bulletBtn);
    
    const orderedBtn = document.createElement('button');
    orderedBtn.textContent = '번호 매기기';
    styleMenuItem(orderedBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 6h11M10 12h11M10 18h11M4 6h1v4M4 10h2M4 18h3M4 14h2v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(orderedBtn, isNodeType(editor, node, 'orderedList'));
    orderedBtn.onclick = () => {
      try {
        editor.chain().focus().toggleOrderedList().run();
      } catch (error) {
        console.error('번호 매기기 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(orderedBtn);
    
    const tasksBtn = document.createElement('button');
    tasksBtn.textContent = '할 일 목록';
    styleMenuItem(tasksBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 12l2 2 4-4M8 6h13M8 18h13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><rect x="3" y="6" width="4" height="4" rx="1" stroke="currentColor" stroke-width="2"/><rect x="3" y="16" width="4" height="4" rx="1" stroke="currentColor" stroke-width="2"/></svg>');
    tasksBtn.onclick = () => {
      try {
        editor.chain().focus().toggleTaskList().run();
      } catch (error) {
        console.error('할 일 목록 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(tasksBtn);
    
    addDivider(menu);
    
    const codeBlockBtn = document.createElement('button');
    codeBlockBtn.textContent = '코드블록';
    styleMenuItem(codeBlockBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 3H7C5.89543 3 5 3.89543 5 5V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V5C19 3.89543 18.1046 3 17 3H16M8 3V5H16V3M8 3H16M10 12L8 14L10 16M14 12L16 14L14 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(codeBlockBtn, isNodeType(editor, node, 'codeBlock'));
    codeBlockBtn.onclick = () => {
      try {
        editor.chain().focus().toggleCodeBlock().run();
      } catch (error) {
        console.error('코드블록 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(codeBlockBtn);
    
    addDivider(menu);
    
    const blockquoteBtn = document.createElement('button');
    blockquoteBtn.textContent = '인용구';
    styleMenuItem(blockquoteBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 11H6V7H10V11ZM14 17H10V13H14V17ZM18 11H14V7H18V11Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(blockquoteBtn, isNodeType(editor, node, 'blockquote'));
    blockquoteBtn.onclick = () => {
      try {
        editor.chain().focus().toggleBlockquote().run();
      } catch (error) {
        console.error('인용구 변환 중 오류:', error);
      }
      closeMenu();
    };
    menu.appendChild(blockquoteBtn);
    
    document.body.appendChild(menu);
    
    setTimeout(() => {
      const menuRect = menu.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      
      if (menuRect.bottom > viewportHeight) {
        menu.style.top = (y - menuRect.height - 10) + 'px';
        menu.style.transform = 'translateY(0)';
      }
      
      if (menuRect.right > viewportWidth) {
        menu.style.left = (viewportWidth - menuRect.width - 10) + 'px';
      }
    }, 0);
    
    function handleClickOutside(e) {
      if (!menu.contains(e.target)) {
        closeMenu();
      }
    }
    currentClickOutsideHandler = handleClickOutside;
    document.addEventListener('mousedown', handleClickOutside);
    
    function closeMenu() {
      menu.remove();
      document.removeEventListener('mousedown', currentClickOutsideHandler);
      currentClickOutsideHandler = null;
      currentOpenMenu = null;
      
      if (typeof openSidebarCallback === 'function') {
        openSidebarCallback();
      }
    }
    
    currentOpenMenu = menu;
    
    return { closeMenu };
  }

</script>

<script>
  // This component doesn't need to render anything, it's just a module to export functions
</script>

<style>
  :global(.line-icon) {
    position: absolute;
    left: -5px;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s, background-color 0.2s;
    border-radius: 4px;
    cursor: pointer;
    color: #555;
  }

  :global(.heading1-line-icon) {
    transform: translateY(+140%);
  }

  :global(.heading2-line-icon) {
    transform: translateY(+40%);
  }

  :global(.heading3-line-icon) {
    transform: translateY(0%);
  }

  :global(.codeBlock-line-icon) {
    transform: translateY(+150%);
  }

  :global(.dark) :global(.line-icon) {
    color: #e5e7eb;
  }
  
  :global(.add-line-icon) {
    position: absolute;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s, background-color 0.2s;
    border-radius: 4px;
    cursor: pointer;
    color: #555;
  }
  
  :global(.dark) :global(.add-line-icon) {
    color: #e5e7eb;
  }
  
  :global(.line-block:hover .line-icon),
  :global(.line-block:hover .add-line-icon) {
    opacity: 0.7;
  }
  
  :global(.line-icon:hover),
  :global(.add-line-icon:hover) {
    opacity: 1 !important;
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  :global(.dark) :global(.line-icon:hover),
  :global(.dark) :global(.add-line-icon:hover) {
    background-color: rgba(255, 255, 255, 0.2);
    color: #ffffff;
  }
  
  /* 메뉴 스타일 */
  :global(#line-menu-popup),
  :global(#add-menu-popup) {
    animation: fadeIn 0.15s ease-in-out;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    border: 1px solid #eee;
    background-color: #fff;
  }
  
  :global(.dark) :global(#line-menu-popup),
  :global(.dark) :global(#add-menu-popup) {
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    border: 1px solid #4B5563;
    background-color: #111827;
  }
  
  :global(#line-menu-popup button),
  :global(#add-menu-popup button) {
    display: flex;
    align-items: center;
    gap: 2px;
    width: 100%;
    text-align: left;
    padding: 6px 8px;
    border: none;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
    color: #333;
  }
  
  :global(.dark) :global(#line-menu-popup button),
  :global(.dark) :global(#add-menu-popup button) {
    color: #e5e7eb;
  }
  
  :global(#line-menu-popup button:hover),
  :global(#add-menu-popup button:hover) {
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  :global(.dark) :global(#line-menu-popup button:hover),
  :global(.dark) :global(#add-menu-popup button:hover) {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  :global(#line-menu-popup button.active),
  :global(#add-menu-popup button.active) {
    background-color: rgba(0, 0, 0, 0.08);
    font-weight: 500;
  }
  
  :global(.dark) :global(#line-menu-popup button.active),
  :global(.dark) :global(#add-menu-popup button.active) {
    background-color: rgba(255, 255, 255, 0.2);
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(5px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  :global(.line-block) {
    position: relative;
    margin-left: 5px;
    padding-left: 5px;
    border-radius: 3px;
    transition: background-color 0.2s ease;
  }
</style> 