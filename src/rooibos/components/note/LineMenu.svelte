<script context="module">
  // Functions exported from the module context can be imported by other files
  export function createLineIcon() {
    const icon = document.createElement('div');
    icon.className = 'line-icon';
    
    // Create three dots vertically
    for (let i = 0; i < 3; i++) {
      const dot = document.createElement('div');
      dot.className = 'line-icon-dot';
      icon.appendChild(dot);
    }
    
    // Apply icon styles
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
    
    return icon;
  }

  // 새로운 함수: + 버튼 아이콘 생성
  export function createAddIcon() {
    const icon = document.createElement('div');
    icon.className = 'add-line-icon';
    
    // Create + symbol
    const plusSymbol = document.createElement('div');
    plusSymbol.className = 'plus-symbol';
    plusSymbol.textContent = '+';
    icon.appendChild(plusSymbol);
    
    // Apply icon styles
    icon.style.cursor = 'pointer';
    icon.style.userSelect = 'none';
    icon.style.display = 'flex';
    icon.style.alignItems = 'center';
    icon.style.justifyContent = 'center';
    icon.style.padding = '4px';
    icon.style.position = 'absolute';
    icon.style.left = '-24px';
    icon.style.top = 'calc(100% - 5px)';
    icon.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
    icon.style.borderRadius = '50%';
    icon.style.zIndex = '10';
    icon.style.width = '18px';
    icon.style.height = '18px';
    icon.style.opacity = '0';
    icon.style.transition = 'opacity 0.2s';
    icon.style.fontSize = '16px';
    icon.style.fontWeight = 'bold';
    icon.style.color = '#666';
    
    return icon;
  }

  // Function to check node type
  function isNodeType(editor, node, type, attrs = {}) {
    if (!editor || !node) return false;
    
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
  }

  // Menu item styling function
  function styleMenuItem(btn, icon) {
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
  }

  // Menu item active styling function
  function styleActiveMenuItem(btn, isActive) {
    if (isActive) {
      btn.style.background = '#f0f0f0';
      btn.style.fontWeight = 'bold';
      
      // Add check icon
      const checkIcon = document.createElement('span');
      checkIcon.innerHTML = '✓';
      checkIcon.style.marginLeft = 'auto';
      checkIcon.style.color = '#4caf50';
      btn.appendChild(checkIcon);
    }
  }

  // Add divider function
  function addDivider(menu) {
    const divider = document.createElement('div');
    divider.style.height = '1px';
    divider.style.background = '#eee';
    divider.style.margin = '4px 0';
    menu.appendChild(divider);
  }

  // Show line menu function
  export function showLineMenu(x, y, editor, node, pos, openSidebarCallback) {
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
    
    // Block conversion section
    const blockHeader = document.createElement('div');
    blockHeader.style.fontSize = '12px';
    blockHeader.style.color = '#888';
    blockHeader.style.padding = '4px 8px';
    menu.appendChild(blockHeader);
    
    const fromPos = pos + 1;
    const toPos = pos + node.nodeSize - 1;
    
    // Paragraph
    const paragraphBtn = document.createElement('button');
    paragraphBtn.textContent = 'Paragraph';
    styleMenuItem(paragraphBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 6v12M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(paragraphBtn, isNodeType(editor, node, 'paragraph'));
    paragraphBtn.onclick = () => {
      editor
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
    styleActiveMenuItem(heading1Btn, isNodeType(editor, node, 'heading', { level: 1 }));
    heading1Btn.onclick = () => {
      editor
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
    styleActiveMenuItem(heading2Btn, isNodeType(editor, node, 'heading', { level: 2 }));
    heading2Btn.onclick = () => {
      editor
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
    styleActiveMenuItem(heading3Btn, isNodeType(editor, node, 'heading', { level: 3 }));
    heading3Btn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection({ from: fromPos, to: toPos })
        .setNode('heading', { level: 3 })
        .run();
      closeMenu();
    };
    menu.appendChild(heading3Btn);
    
    // Add divider before list options
    addDivider(menu);
    
    // Bullet list
    const bulletBtn = document.createElement('button');
    bulletBtn.textContent = 'Bullet list';
    styleMenuItem(bulletBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    styleActiveMenuItem(bulletBtn, isNodeType(editor, node, 'bulletList'));
    bulletBtn.onclick = () => {
      editor
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
    styleActiveMenuItem(orderedBtn, isNodeType(editor, node, 'orderedList'));
    orderedBtn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection({ from: fromPos, to: toPos })
        .toggleOrderedList()
        .run();
      closeMenu();
    };
    menu.appendChild(orderedBtn);
    
    addDivider(menu);
    
    // AI section
    // Ask AI
    const askAI = document.createElement('button');
    askAI.textContent = 'Ask AI';
    styleMenuItem(askAI, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2a10 10 0 1 0 10 10 10 10 0 0 0-10-10zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8zm0-13a1 1 0 0 0-1 1v5a1 1 0 0 0 2 0V8a1 1 0 0 0-1-1zm0 10a1.5 1.5 0 1 0-1.5-1.5A1.5 1.5 0 0 0 12 17z" fill="currentColor"/></svg>');
    askAI.onclick = () => {
      closeMenu();
      if (openSidebarCallback) {
        openSidebarCallback();
      }
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
    
    return { closeMenu };
  }

  // 새로운 함수: + 버튼 클릭 시 메뉴 표시
  export function showAddMenu(x, y, editor, pos) {
    const oldMenu = document.getElementById('add-menu-popup');
    if (oldMenu) {
      oldMenu.remove();
    }
    
    const menu = document.createElement('div');
    menu.id = 'add-menu-popup';
    menu.style.position = 'absolute';
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
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
    
    // 새 텍스트 블록 추가
    const textBtn = document.createElement('button');
    textBtn.textContent = 'Text';
    styleMenuItem(textBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 6v12M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    textBtn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection(pos)
        .insertContent('<p></p>')
        .run();
      closeMenu();
    };
    menu.appendChild(textBtn);
    
    // 헤딩 1 추가
    const h1Btn = document.createElement('button');
    h1Btn.textContent = 'Heading 1';
    styleMenuItem(h1Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    h1Btn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection(pos)
        .insertContent('<h1></h1>')
        .run();
      closeMenu();
    };
    menu.appendChild(h1Btn);
    
    // 헤딩 2 추가
    const h2Btn = document.createElement('button');
    h2Btn.textContent = 'Heading 2';
    styleMenuItem(h2Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    h2Btn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection(pos)
        .insertContent('<h2></h2>')
        .run();
      closeMenu();
    };
    menu.appendChild(h2Btn);
    
    // 헤딩 3 추가
    const h3Btn = document.createElement('button');
    h3Btn.textContent = 'Heading 3';
    styleMenuItem(h3Btn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 4v16M18 4v16M6 12h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    h3Btn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection(pos)
        .insertContent('<h3></h3>')
        .run();
      closeMenu();
    };
    menu.appendChild(h3Btn);
    
    addDivider(menu);
    
    // 불릿 리스트 추가
    const bulletBtn = document.createElement('button');
    bulletBtn.textContent = 'Bullet list';
    styleMenuItem(bulletBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    bulletBtn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection(pos)
        .insertContent('<ul><li></li></ul>')
        .run();
      closeMenu();
    };
    menu.appendChild(bulletBtn);
    
    // 순서 리스트 추가
    const orderedBtn = document.createElement('button');
    orderedBtn.textContent = 'Ordered list';
    styleMenuItem(orderedBtn, '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 6h11M10 12h11M10 18h11M4 6h1v4M4 10h2M4 18h3M4 14h2v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    orderedBtn.onclick = () => {
      editor
        .chain()
        .focus()
        .setTextSelection(pos)
        .insertContent('<ol><li></li></ol>')
        .run();
      closeMenu();
    };
    menu.appendChild(orderedBtn);
    
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
    
    return { closeMenu };
  }
</script>

<script>
  // This component doesn't need to render anything, it's just a module to export functions
</script>

<style>
  /* Line icon styles */
  :global(.line-icon) {
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

  :global(.line-icon:hover) {
    background-color: rgba(0, 0, 0, 0.1);
    opacity: 1 !important;
  }

  :global(.line-icon-dot) {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background-color: #666;
  }

  /* 새로운 스타일: + 버튼 아이콘 */
  :global(.add-line-icon) {
    opacity: 0; 
    transition: opacity 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    position: absolute;
    left: -24px;
    top: calc(100% - 5px);
    padding: 2px;
    background-color: rgba(0, 0, 0, 0.05);
    border-radius: 50%;
    z-index: 10;
    width: 18px;
    height: 18px;
    font-size: 16px;
    font-weight: bold;
    color: #666;
  }

  :global(.add-line-icon:hover) {
    background-color: rgba(0, 0, 0, 0.1);
    opacity: 1 !important;
  }

  :global(.line-block) {
    position: relative;
    margin-left: 10px;
    padding-left: 5px;
    border-radius: 3px;
    transition: background-color 0.2s ease;
  }

  :global(.line-block:hover) {
    background-color: rgba(0, 0, 0, 0.02);
  }
  
  :global(.line-block:hover .line-icon) {
    opacity: 1;
  }
  
  :global(.line-block:hover .add-line-icon) {
    opacity: 1;
  }
  
  /* Menu styles */
  :global(#line-menu-popup button) {
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

  :global(#line-menu-popup button:hover) {
    background: #f5f5f5;
  }
  
  :global(#add-menu-popup button) {
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

  :global(#add-menu-popup button:hover) {
    background: #f5f5f5;
  }
</style> 