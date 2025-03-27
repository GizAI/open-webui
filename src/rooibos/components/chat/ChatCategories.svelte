<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { models , user } from '$lib/stores';	
	
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
		tags = Array.from(new Set(tags)).sort((a, b) => a.localeCompare(b));
		
		// 태그가 없는 모델을 위한 "기타" 카테고리 추가
		tags.push("기타");
		
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
			filteredItems = categories[activeCategoryIndex]?.items.map(item => ({
				...item,
				categoryTitle: categories[activeCategoryIndex].title
			})) || [];
		}
	}

	// 모델의 태그 정보를 안전하게 가져오는 헬퍼 함수
	function getModelTags(model: any) {
		return model?.info?.meta?.tags || [];
	}

	// 모델이 태그를 가지고 있는지 확인하는 헬퍼 함수
	function hasModelTags(model: any) {
		const tags = getModelTags(model);
		return tags && tags.length > 0;
	}

	// 현재 선택된 대분류 인덱스 (기본값 0)
	let activeCategoryIndex: number = 0;

	// 모바일 여부: 창 너비가 768px 미만이면 모바일로 간주
	let isMobile = false;
	let containerHeight = 0;
	let parentHeight = 0;

	// 하위 아이템 클릭 시 상위에 이벤트 전달
	function selectSubItem(item: SubItem) {
		dispatch('select', item.model);
		show = false;
	}
</script>

<Modal size="xl" bind:show>
	<div class="text-gray-700 dark:text-gray-100 {isMobile ? 'h-screen' : ''}">
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class="text-lg font-medium self-center">지식 전문 봇</div>
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
			<div class="m-auto w-full px-8 lg:px-20 py-6 categories-container {isMobile ? 'h-[calc(100vh-4rem)]' : ''}">
				<div class="mb-4">
					<div class="mt-2">
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="모델 이름 또는 설명으로 검색"
							class="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
				</div>
				<div class="flex flex-col md:flex-row gap-4 items-start md:min-h-[500px]">
					{#if !searchQuery}
						{#if isMobile}
							<div class="w-full">
								<select
									class="w-full px-4 py-2 mb-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100"
									bind:value={activeCategoryIndex}
								>
									{#each categories as category, index}
										<option value={index}>
											{category.title} ({category.items.length}개)
										</option>
									{/each}
								</select>
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
					<div class="{searchQuery ? 'w-full' : 'md:w-2/3'} {isMobile ? 'h-[calc(100vh-12rem)]' : 'md:max-h-[500px]'} md:overflow-y-auto">
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
											<div class="flex items-center">
												<img 
													src={item.model?.info?.meta?.profile_image_url ?? '/static/favicon.png'} 
													alt="Model" 
													class="rounded-full w-5 h-5 mr-2"
												/>
												<div class="font-medium text-gray-800 dark:text-gray-100">{item.title}</div>
											</div>
											{#if hasModelTags(item.model) && !searchQuery}
												<div class="flex flex-wrap gap-1 mt-1">
													{#each getModelTags(item.model) as tag}
														<span class="text-xs font-bold px-1 rounded-sm uppercase bg-gray-500/20 text-gray-700 dark:text-gray-200">
															{tag.name}
														</span>
													{/each}
												</div>
											{/if}
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
				<p class="text-gray-600 dark:text-gray-400">사용 가능한 모델이 없습니다.</p>
			</div>
		{/if}
	</div>
</Modal>
