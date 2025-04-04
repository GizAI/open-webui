<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { models , user, config } from '$lib/stores';	
	
	import Fuse from 'fuse.js';

	const dispatch = createEventDispatcher();

	export let show = false;

	// 검색어 상태 변수
	let searchQuery = '';
	let fuse: Fuse<SubItem> | null = null;
	let filteredItems: SubItem[] = [];

	// 하위 아이템 타입 (모델)
	type SubItem = {
		title: string;
		description: string;
		model_id: string;
		categoryTitle?: string;
		model: any;
	};

	// 카테고리 타입 (태그)
	type Category = {
		title: string;
		items: SubItem[];
	};

	// 카테고리 데이터를 저장할 변수
	let categories: Category[] = [];
	
	// 태그 목록
	let tags: string[] = [];

	// 관리자가 정의한 태그 순서
	const TAG_ORDER = [
		"개척화법",
		"법인컨설팅",
		"정부지원사업",
		"세금공제감면",
		"법인절세",
		"가업승계절세",
		"보고서"
	];

	// models 스토어에서 태그 정보를 추출하여 카테고리 생성
	function generateCategoriesFromTags() {
		// base_model_id가 있는 모델만 필터링
		const validModels = $models.filter(model => model?.info?.base_model_id);
		
		// 접근 제어가 있는 모델과 없는 모델 분리
		const publicModels = validModels.filter(model => (model?.info as any)?.access_control === null);
		const privateModels = validModels.filter(model => {
			const info = model?.info as any;
			return info?.access_control !== null && info?.user_id === ($user?.id ?? null);
		});

		// 공개 모델에서 태그 추출
		tags = publicModels
			.flatMap(model => {
				const meta = model?.info?.meta as any;
				return meta?.tags ?? [];
			})
			.map(tag => tag.name)
			.filter(Boolean);
		
		// 중복 제거 및 정렬
		tags = Array.from(new Set(tags)).sort((a, b) => {
			// "기타" 카테고리는 항상 마지막
			if (a === "기타") return 1;
			if (b === "기타") return -1;
			
			// TAG_ORDER에 정의된 순서 사용
			const indexA = TAG_ORDER.indexOf(a);
			const indexB = TAG_ORDER.indexOf(b);
			
			// TAG_ORDER에 없는 태그는 맨 뒤로 (기타 카테고리 앞)
			if (indexA === -1 && indexB === -1) return a.localeCompare(b);
			if (indexA === -1) return 1;
			if (indexB === -1) return -1;
			
			return indexA - indexB;
		});
		
		// 태그가 없는 모델을 위한 "기타" 카테고리 추가
		if (!tags.includes("기타")) {
			tags.push("기타");
		}
		
		// 카테고리 배열 초기화
		categories = [];

		// 개인 모델이 있다면 "나의 모델" 카테고리 추가
		if (privateModels.length > 0) {
			categories.push({
				title: "나의 모델",
				items: privateModels.map(model => ({
					title: model.name,
					description: model.info?.meta?.description || "",
					model_id: model.id,
					model: model
				}))
			});
		}

		// 공개 모델에 대한 카테고리 생성
		const publicCategories = tags.map(tag => {
			const tagModels = tag === "기타" 
				? publicModels.filter(model => {
					const meta = model?.info?.meta as any;
					return !meta?.tags || meta.tags.length === 0;
				})
				: publicModels.filter(model => {
					const meta = model?.info?.meta as any;
					return meta?.tags?.some((modelTag: any) => modelTag.name === tag);
				});
			
			const items = tagModels.map(model => ({
				title: model.name,
				description: model.info?.meta?.description || "",
				model_id: model.id,
				model: model
			}));
			
			return {
				title: tag,
				items
			};
		}).filter(category => category.items.length > 0);

		// 공개 카테고리를 기존 카테고리 배열에 추가
		categories = [...categories, ...publicCategories];
		
		// 카테고리가 생성된 후 높이 업데이트
		setTimeout(updateHeight, 0);
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
		generateCategoriesFromTags();
		
		window.addEventListener('resize', () => {
			checkMobile();
			updateHeight();
		});
		
		return () => {
			window.removeEventListener('resize', checkMobile);
			window.removeEventListener('resize', updateHeight);
		};
	});

	// models 스토어가 변경될 때마다 카테고리 재생성
	$: if ($models) {
		generateCategoriesFromTags();
	}

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
			if (activeCategoryIndex !== null && categories[activeCategoryIndex]) {
				const category = categories[activeCategoryIndex];
				filteredItems = category.items.map(item => ({
					...item,
					categoryTitle: category.title
				}));
			} else {
				filteredItems = [];
			}
		}
	}

	// 모델의 태그 정보를 안전하게 가져오는 헬퍼 함수
	function getModelTags(model: any) {
		return model?.info?.meta?.tags || [];
	}


	// 현재 선택된 대분류 인덱스 (기본값 null)
	let activeCategoryIndex: number | null = null;

	// 모바일 여부: 창 너비가 768px 미만이면 모바일로 간주
	let isMobile = false;
	let containerHeight = 0;
	let parentHeight = 0;
	
	// 모바일용 드롭다운 상태
	let isDropdownOpen = false;

	// 하위 아이템 클릭 시 상위에 이벤트 전달
	function selectSubItem(item: SubItem) {
		dispatch('select', item.model);
		show = false;
	}
	
	// 카테고리 선택
	function selectCategory(index: number) {
		activeCategoryIndex = index;
		isDropdownOpen = false;
	}

	// 기본 모델 선택 핸들러 추가
	function selectDefaultModel() {
		const defaultModel = $config?.default_models.split(',')[0];
		let model = $models.find((m) => m.id === defaultModel);
		if(!model){
			model = $models.find((m) => m.info?.base_model_id == null);
		}
		if(model) {
			dispatch('select', model);
			show = false;
		}
	}

	// 모달이 열릴 때 카테고리 선택 초기화
	$: if (show) {
		activeCategoryIndex = null;
		isDropdownOpen = false;
	}
</script>

<Modal size="xl" bind:show>
	<div class="text-gray-700 dark:text-gray-100 {isMobile ? 'h-screen flex flex-col' : ''}">
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1 {isMobile ? 'flex-shrink-0' : ''}">
			<div class="text-lg font-medium self-center">지식 전문 봇</div>
			<div class="flex items-center gap-2">
				<button
					class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm transition-colors"
					on:click={selectDefaultModel}
				>
					선택 취소
				</button>
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
		</div>

		{#if categories.length > 0}
			<div class="m-auto w-full {isMobile ? 'px-4 py-4 flex-1 overflow-hidden flex flex-col' : 'px-8 lg:px-20 py-6'} categories-container">
				<div class="mb-4 {isMobile ? 'flex-shrink-0' : ''}">
					<div class="mt-2">
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="모델 이름 또는 설명으로 검색"
							class="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
				</div>
				<div class="flex flex-col md:flex-row gap-4 items-start md:min-h-[500px] {isMobile ? 'flex-1 overflow-hidden' : ''}">
					{#if !searchQuery}
						{#if isMobile}
							<div class="w-full relative mb-4 flex-shrink-0">
								<!-- 커스텀 드롭다운 -->
								<button 
									class="w-full flex justify-between items-center px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
									on:click={() => isDropdownOpen = !isDropdownOpen}
								>
									<span>{activeCategoryIndex !== null ? categories[activeCategoryIndex].title : '분류를 선택하세요'}</span>
									<svg class="w-4 h-4 fill-current text-gray-500 dark:text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
										<path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
									</svg>
								</button>
								
								{#if isDropdownOpen}
									<div class="absolute z-10 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
										<div class="max-h-60 overflow-y-auto">
											{#each categories as category, index}
												<button 
													class="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 {activeCategoryIndex === index ? 'bg-gray-100 dark:bg-gray-700' : ''}"
													on:click={() => selectCategory(index)}
												>
													<div class="font-medium text-gray-800 dark:text-gray-100">{category.title}</div>
													<div class="text-xs text-gray-500 dark:text-gray-400">{category.items.length}개 모델</div>
												</button>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						{:else}
							<div class="md:w-1/3 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden md:max-h-[500px] md:overflow-y-auto">
								{#each categories as category, index}
									<button
										type="button"
										class="w-full text-left p-4 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition {activeCategoryIndex === index ? 'bg-gray-100 dark:bg-gray-800' : ''}"
										on:mouseenter={() => { if (!isMobile) activeCategoryIndex = index; }}
										on:click={() => activeCategoryIndex = index}
									>
										<div class="font-semibold text-gray-800 dark:text-gray-100">{category.title}</div>
										<div class="text-xs text-gray-500 dark:text-gray-400">{category.items.length}개 모델</div>
									</button>
								{/each}
							</div>
						{/if}
					{/if}

					<!-- 모델 목록 (2단계) -->
					<div class="{searchQuery ? 'w-full' : 'md:w-2/3'} {isMobile ? 'flex-1 overflow-y-auto w-full' : 'md:max-h-[500px]'} md:overflow-y-auto">
						{#if filteredItems.length === 0}
							<div class="text-center p-4 text-gray-500 dark:text-gray-400">
								검색 결과가 없습니다.
							</div>
						{:else}
							<div class="{isMobile ? 'flex flex-col w-full pb-2' : 'grid grid-cols-1 sm:grid-cols-2 gap-3 p-1'}">
								{#each filteredItems as item (item.title)}
									<button
										class="w-full text-left p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition {isMobile ? 'mb-2' : ''}"
										on:click={() => selectSubItem(item)}
									>
										<div class="flex flex-col w-full">
											{#if searchQuery}
												<div class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{item.categoryTitle}</div>
											{/if}
											<div class="flex items-center w-full">
												<img 
													src={item.model?.info?.meta?.profile_image_url ?? '/static/favicon.png'} 
													alt="Model" 
													class="rounded-full w-4 h-4 mr-2 flex-shrink-0"
												/>
												<div class="font-medium text-gray-800 dark:text-gray-100 text-sm truncate">{item.title}</div>
											</div>
											<div class="mt-0.5 text-xs text-gray-500 dark:text-gray-400 line-clamp-2 w-full">{item.description}</div>
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
				<p class="text-gray-600 dark:text-gray-400">사용 가능한 모델이 없습니다.</p>
			</div>
		{/if}
	</div>
</Modal>
