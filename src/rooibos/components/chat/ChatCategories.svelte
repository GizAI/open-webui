<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { fade } from 'svelte/transition';
    import { WEBUI_API_BASE_URL } from '$lib/constants';
	import Modal from '$lib/components/common/Modal.svelte';
	import { getModelById } from '$lib/apis/models';
	import Fuse from 'fuse.js';

	const dispatch = createEventDispatcher();

	export let show = false;

	// 검색어 상태 변수
	let searchQuery = '';
	let fuse: Fuse<SubItem> | null = null;
	let filteredItems: SubItem[] = [];

	// 하위 아이템 타입
	type SubItem = {
		title: string;
		description: string;
		model_id: string;
		categoryTitle?: string;
	};

	// 카테고리 타입 (대분류)
	type Category = {
		title: string;
		items: SubItem[];
	};

	// 카테고리 데이터를 저장할 변수
	let categories: Category[] = [];
	
	// DB로부터 카테고리 데이터 가져오기
	async function fetchCategories() {
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/categories/2`);
			if (!response.ok) {
				throw new Error('카테고리 데이터를 가져오는데 실패했습니다.');
			}
			const data = await response.json();
			categories = data.data.categories;
			// 카테고리 데이터가 로드된 후 다음 프레임에서 높이 업데이트
			setTimeout(updateHeight, 0);
		} catch (error) {
			console.error('카테고리 데이터 로딩 에러:', error);
		}
	}

	function updateHeight() {
		const parent = document.documentElement;
		parentHeight = parent.clientHeight;
		const container = document.querySelector('.categories-container');
		if (container) {
			containerHeight = container.clientHeight;
		}
	}

	onMount(() => {
		const checkMobile = () => {
			isMobile = window.innerWidth < 768;
		};

		checkMobile();
		fetchCategories();
		
		window.addEventListener('resize', () => {
			checkMobile();
			updateHeight();
		});
		
		return () => {
			window.removeEventListener('resize', checkMobile);
			window.removeEventListener('resize', updateHeight);
		};
	});

	// categories가 변경될 때마다 높이 업데이트하고 Fuse 인스턴스 생성
	$: {
		if (categories.length > 0) {
			setTimeout(updateHeight, 0);
			// 모든 하위 아이템을 하나의 배열로 합치기
			const allItems = categories.reduce((acc, category) => [...acc, ...category.items], [] as SubItem[]);
			// Fuse 인스턴스 생성
			fuse = new Fuse(allItems, {
				keys: ['title', 'description'],
				threshold: 0.3
			});
		}
	}

	// 검색어가 변경될 때마다 필터링된 아이템 업데이트
	$: {
		if (fuse && searchQuery) {
			// 검색 결과에 카테고리 정보 추가
			filteredItems = fuse.search(searchQuery).map(result => {
				const item = result.item;
				// 아이템이 속한 카테고리 찾기
				const category = categories.find(cat => cat.items.some(i => i.title === item.title));
				return {
					...item,
					categoryTitle: category?.title || ''
				};
			});
		} else {
			filteredItems = categories[activeCategoryIndex]?.items.map(item => ({
				...item,
				categoryTitle: categories[activeCategoryIndex].title
			})) || [];
		}
	}

	// 현재 선택된 대분류 인덱스 (기본값 0)
	let activeCategoryIndex: number = 0;

	// 모바일 여부: 창 너비가 768px 미만이면 모바일로 간주
	let isMobile = false;
	let containerHeight = 0;
	let parentHeight = 0;

	// 하위 아이템 클릭 시 상위에 이벤트 전달
	async function selectSubItem(item: SubItem) {
		const selectedModel = await getModelById(localStorage.token, item.model_id);
		dispatch('select', selectedModel);
		show = false;
	}
</script>

<Modal size="xl" bind:show>
	<div class="text-gray-700 dark:text-gray-100">
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class="text-lg font-medium self-center">카테고리 선택</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		{#if categories.length > 0}
			<div class="m-auto w-full px-8 lg:px-20 py-6 categories-container">
				<!-- 헤더 -->
				<div class="mb-4">
					<p class="text-gray-600 dark:text-gray-400 text-sm">원하는 항목을 선택하세요.</p>
					<!-- 검색 입력창 추가 -->
					<div class="mt-2">
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="제목 또는 설명으로 검색"
							class="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
				</div>

				<!-- flex 컨테이너 -->
				<div class="flex flex-col md:flex-row gap-4 items-start md:min-h-[500px]">
					<!-- 대분류 목록 (1단계) - 검색 중이 아닐 때만 표시 -->
					{#if !searchQuery}
						<div class="md:w-1/3 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden md:max-h-[500px] md:overflow-y-auto">
							{#each categories as category, index}
								<button
									type="button"
									class="w-full text-left p-4 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition {activeCategoryIndex === index ? 'bg-gray-100 dark:bg-gray-800' : ''}"
									on:mouseenter={() => { if (!isMobile) activeCategoryIndex = index; }}
									on:click={() => activeCategoryIndex = index}
								>
									<div class="font-semibold text-gray-800 dark:text-gray-100">{category.title}</div>
								</button>
							{/each}
						</div>
					{/if}

					<!-- 중분류 목록 (2단계) -->
					<div class="{searchQuery ? 'w-full' : 'md:w-2/3'} md:max-h-[500px] md:overflow-y-auto">
						{#if filteredItems.length === 0}
							<div class="text-center p-4 text-gray-500 dark:text-gray-400">
								검색 결과가 없습니다.
							</div>
						{:else}
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 p-1">
								{#each filteredItems as item (item.title)}
									<button
										class="w-full text-left p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
										on:click={() => selectSubItem(item)}
									>
										<div class="flex flex-col">
											{#if searchQuery}
												<div class="text-xs text-gray-500 dark:text-gray-400 mb-1">{item.categoryTitle}</div>
											{/if}
											<div class="font-medium text-gray-800 dark:text-gray-100">{item.title}</div>
											<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">{item.description}</div>
										</div>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>
		{:else}
			<div class="flex justify-center items-center h-full p-8">
				<p class="text-gray-600 dark:text-gray-400">카테고리를 불러오는 중...</p>
			</div>
		{/if}
	</div>
</Modal>

<style>
	/* 필요에 따라 추가적인 커스텀 스타일 작성 */
</style>
