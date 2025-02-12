<!-- ChatPlaceholder.svelte -->
<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	// 하위 아이템 타입
	type SubItem = {
		title: string;
		description: string;
	};

	// 카테고리 타입 (대분류) – 최상위 분류 설명은 제거
	type Category = {
		title: string;
		items: SubItem[];
	};

	// JSON 형태로 정의된 카테고리 데이터
	const categoriesJSON = `
	[
		{
			"title": "개척화법",
			"items": [
				{ "title": "일 반", "description": "일반 반에 관한 간단한 설명입니다." },
				{ "title": "단 체 보 험", "description": "단체 보험의 기본 개념 및 적용 방법에 대한 설명입니다." },
				{ "title": "법인컨설팅", "description": "법인컨설팅의 주요 서비스와 특징에 대한 설명입니다." },
				{ "title": "정보지원금", "description": "정보지원금의 신청 및 지원 내용을 간략히 설명합니다." },
				{ "title": "TA 단체보험", "description": "TA 단체보험의 혜택 및 적용 사례에 대한 설명입니다." },
				{ "title": "TA 단체보험(Remodeling)", "description": "리모델링된 TA 단체보험의 특징과 장점을 설명합니다." }
			]
		},
		{
			"title": "법인컨설팅",
			"items": [
				{ "title": "법인 설립", "description": "법인 설립 절차 및 유의사항에 대한 설명입니다." },
				{ "title": "정관 제 / 개정", "description": "정관 작성 및 개정의 기본 원칙을 설명합니다." },
				{ "title": "개인사업자 법인 전환", "description": "개인사업자를 법인으로 전환하는 방법에 대한 설명입니다." },
				{ "title": "법인 분할 / 합병 / 회생 / 청산", "description": "법인의 분할, 합병, 회생 및 청산 절차를 간단히 설명합니다." },
				{ "title": "기업지배구조 - 이사회 - 주주총회", "description": "기업 지배구조와 이사회, 주주총회의 역할에 대한 설명입니다." },
				{ "title": "상속 : 유언  유언대응신탁", "description": "상속 및 유언, 유언대응신탁의 기본 개념을 설명합니다." },
				{ "title": "상속세 및 증여세법", "description": "상속세와 증여세법의 주요 내용을 간략히 설명합니다." },
				{ "title": "임원소득 보상(급여 / 상여 등)", "description": "임원 소득 보상 방식(급여, 상여 등)을 설명합니다." },
				{ "title": "임원소득보상(배당)", "description": "배당을 통한 임원 소득 보상에 대해 설명합니다." },
				{ "title": "임원소득보상(퇴직금 및 유족보상)", "description": "퇴직금 및 유족보상 관련 내용을 다룹니다." }
			]
		},
		{
			"title": "정부지원사업",
			"items": [
				{ "title": "중소기업 고용지원 제도", "description": "중소기업의 고용 지원 제도에 대한 설명입니다." },
				{ "title": "기업인증제도 : 기업부설연구소", "description": "기업부설연구소 관련 인증 제도를 설명합니다." },
				{ "title": "기업인증제도 : 벤처, 이노비즈, 메인비즈, NET", "description": "다양한 기업인증 제도에 대해 간략히 설명합니다." },
				{ "title": "소상공인정책자금", "description": "소상공인 정책자금의 신청 및 지원 내용을 설명합니다." },
				{ "title": "중진공정책자금", "description": "중진공 정책자금의 주요 내용과 지원 대상을 설명합니다." }
			]
		},
		{
			"title": "세금공제감면",
			"items": [
				{ "title": "성과 공유제", "description": "성과 공유제의 기본 개념과 효과에 대해 설명합니다." },
				{ "title": "사내근로복지기금", "description": "사내 근로복지기금의 활용 방법과 혜택을 설명합니다." },
				{ "title": "스톡옵션", "description": "스톡옵션의 구조와 적용 사례에 대한 설명입니다." },
				{ "title": "직무발명보상", "description": "직무발명 보상 제도의 주요 내용을 설명합니다." },
				{ "title": "연구개발", "description": "연구개발 관련 세금 혜택 및 지원 사항을 설명합니다." },
				{ "title": "고용창출", "description": "고용창출 관련 지원 및 감면 제도를 설명합니다." },
				{ "title": "세무조정 및 경정청구", "description": "세무조정 및 경정청구 절차에 대해 설명합니다." },
				{ "title": "보험금 소득세 (종합, 양도, 퇴직소득세)", "description": "보험금 소득세의 종류와 적용 사례를 설명합니다." }
			]
		},
		{
			"title": "법인절세",
			"items": [
				{ "title": "미처분 잉여금", "description": "미처분 잉여금 처리에 관한 기본 사항을 설명합니다." },
				{ "title": "배당 (초과 / 감액배당)", "description": "배당의 초과 및 감액 배당에 대한 설명입니다." },
				{ "title": "가지급금 / 가수금", "description": "가지급금 및 가수금 처리 방법에 대해 설명합니다." },
				{ "title": "기업가치평가 (비상장주식, 부동산, 유무형자산 재평가)", "description": "기업가치평가 방법 및 유의사항을 설명합니다." },
				{ "title": "명의신탁주식 (차명주식)", "description": "명의신탁주식(차명주식)의 개념과 주의점을 설명합니다." },
				{ "title": "증자 / 감자 / 이익소각 / 상속감자", "description": "증자, 감자, 이익소각, 상속감자 절차를 간략히 설명합니다." },
				{ "title": "자기주식 (취득 / 처분 / 소각)", "description": "자기주식의 취득, 처분 및 소각에 관한 설명입니다." },
				{ "title": "CEO 은퇴플랜", "description": "CEO 은퇴플랜의 구성 및 주요 혜택을 설명합니다." }
			]
		},
		{
			"title": "가업승계절세",
			"items": [
				{ "title": "특정 법인", "description": "특정 법인에 관한 기본 사항을 설명합니다." },
				{ "title": "가업상속공제", "description": "가업상속공제 제도의 주요 내용을 설명합니다." },
				{ "title": "가업승계증여특례", "description": "가업승계증여특례의 적용 방법을 설명합니다." },
				{ "title": "창업자금증여특례", "description": "창업자금 증여특례 제도에 대해 간략히 설명합니다." }
			]
		}
	]
	`;

	const categories: Category[] = JSON.parse(categoriesJSON);

	// 현재 선택된 대분류 인덱스 (기본값 0)
	let activeCategoryIndex: number = 0;

	// 모바일 여부: 창 너비가 768px 미만이면 모바일로 간주
	let isMobile = false;
	let containerHeight = 0;
	let parentHeight = 0;

	onMount(() => {
		const checkMobile = () => {
			isMobile = window.innerWidth < 768;
		};
		
		const updateHeight = () => {
			const parent = document.documentElement;
			parentHeight = parent.clientHeight;
			const container = document.querySelector('.categories-container');
			if (container) {
				containerHeight = container.clientHeight;
			}
		};

		checkMobile();
		updateHeight();
		window.addEventListener('resize', () => {
			checkMobile();
			updateHeight();
		});
		
		return () => {
			window.removeEventListener('resize', checkMobile);
			window.removeEventListener('resize', updateHeight);
		};
	});

	$: topMargin = !isMobile ? Math.max(0, (parentHeight - containerHeight) / 4) : 0;

	// 하위 아이템 클릭 시 상위에 이벤트 전달
	function selectSubItem(item: SubItem) {
		dispatch('select', item);
	}
</script>

<div 
	class="m-auto w-full max-w-6xl px-8 lg:px-20 py-6 categories-container" 
	style="margin-top: {topMargin}px;"
>
	<!-- 헤더 -->
	<div class="mb-4">
		<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100">카테고리 선택</h2>
		<p class="text-gray-600 dark:text-gray-400 text-sm">원하는 항목을 선택하세요.</p>
	</div>

	<!-- flex 컨테이너 - 데스크탑에서만 min-h-[500px] 적용 -->
	<div class="flex flex-col md:flex-row gap-4 items-start md:min-h-[500px]">
		<!-- 대분류 목록 (1단계) - 데스크탑에서만 max-h-[500px]와 overflow-y-auto 적용 -->
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

		<!-- 중분류 목록 (2단계) - 데스크탑에서만 max-h-[500px]와 overflow-y-auto 적용 -->
		<div class="md:w-2/3 md:max-h-[500px] md:overflow-y-auto">
			{#if isMobile}
				{#key activeCategoryIndex}
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 p-1" in:fade out:fade>
						{#each categories[activeCategoryIndex].items as item (item.title)}
							<button
								class="w-full text-left p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
								on:click={() => selectSubItem(item)}
							>
								<div class="font-medium text-gray-800 dark:text-gray-100">{item.title}</div>
								<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">{item.description}</div>
							</button>
						{/each}
					</div>
				{/key}
			{:else}
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 p-1">
					{#each categories[activeCategoryIndex].items as item (item.title)}
						<button
							class="w-full text-left p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
							on:click={() => selectSubItem(item)}
						>
							<div class="font-medium text-gray-800 dark:text-gray-100">{item.title}</div>
							<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">{item.description}</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	/* 필요에 따라 추가적인 커스텀 스타일 작성 */
</style>
