export const filterGroups = [
	{
		id: 'radius',
		title: '반경',
		isMulti: false,
		defaultValue: '200',
		options: [
			{ id: '200', label: '200m' },
			{ id: '500', label: '500m' },
			{ id: '1000', label: '1km' },
			{ id: '2000', label: '2km' }
		]
	},
	{
		id: 'sales',
		title: '최근 매출액',
		isMulti: false,
		checked: false,
		min: 0,
		max: 0
	},
	{
		id: 'profit',
		title: '영업이익',
		isMulti: false,
		checked: false,
		min: 0,
		max: 0
	},
	{
		id: 'net_profit',
		title: '당기순이익',
		isMulti: false,
		checked: false,
		min: 0,
		max: 0
	},
	{
		id: 'total_equity',
		title: '총자본',
		isMulti: false,
		checked: false,
		min: 0,
		max: 0
	},
	
	// {
	// 	id: 'unallocated_profit',
	// 	title: '미처분 이익 잉여금',
	// 	isMulti: false,
	// 	checked: false,
	// 	min: 0,
	// 	max: 0
	// },
	{
		id: 'employee_count',
		title: '종업원 수',
		isMulti: false,
		min: 0,
		max: 0
	},
	{
		id: 'certification',
		title: '기업 인증',
		isMulti: true,
		checked: false,
		options: [
			{ id: 'research_institute', label: '연구소 인증' },
			{ id: 'venture', label: '벤처 인증' },
			{ id: 'innobiz', label: '이노비즈 인증' },
			{ id: 'mainbiz', label: '메인비즈 인증' }
			// { id: 'patent', label: '특허 보유' },
			// { id: 'new_technology', label: '신기술' },
		]
	},
	{
		id: 'included_industries',
		title: '업종',
		checked: false
	},
	
	{
		id: 'gender',
		title: '대표이사(남.여)',
		isMulti: false,
		checked: false,
		options: [
			{ id: '', label: '선택없음' },
			{ id: 'male', label: '남자' },
			{ id: 'female', label: '여자' }
		]
	},
	{
		id: 'representative_age',
		title: '대표의 나이',
		isMulti: false,
		checked: false
	},
	
	// {
	// 	id: 'establishment_year',
	// 	title: '법인 설립 연도',
	// 	isMulti: false,
	// 	checked: false
	// },
	// {
	//   id: 'loan',
	//   title: '대출 사용 여부 및 금액',
	//   icon: Building2,
	//   iconClass: "text-blue-500",
	//   isMulti: false,
	//   options: [
	//     { id: 'use_loan', label: '대출 사용' },
	//     { id: 'no_loan', label: '대출 미사용' },
	//     { id: 'under_100m', label: '대출 1억 이하' },
	//     { id: '100m_to_200m', label: '대출 1억 이상 ~ 2억' },
	//     { id: 'over_200m', label: '2억 이상' },
	//   ],
	// },
	
];

export const filterActions = [
	{
		id: 'reset',
		label: '초기화',
		action: 'reset'
	}
];

export const excludedGroupIds = [
	'employee_count',
	'sales',
	'profit',
	'net_profit',
	'unallocated_profit',
	'establishment_year',
	'representative_age',
	'total_equity'
];

export function onFilterChange(selectedFilters: any, groupId: string, optionId: string, checked: boolean | string) {
	let newFilters = { ...selectedFilters };

	if (optionId === 'checked') {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			checked: checked as boolean
		};
	} else if (groupId === 'radius' && typeof checked === 'string') {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			value: checked
		};
	} else if (
		groupId === 'distance' ||
		groupId === 'representative' ||
		groupId === 'gender' ||
		groupId === 'loan'
	) {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			value: checked ? optionId : ''
		};
	} else if (groupId === 'representative_age' || groupId === 'establishment_year') {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			value: checked
		};
	} else if (
		['employee_count', 'sales', 'profit', 'net_profit', 'unallocated_profit', 'total_equity'].includes(groupId) &&
		typeof checked === 'object' &&
		checked !== null
	) {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			...checked
		};
	} else if (groupId === 'included_industries' || groupId === 'excluded_industries') {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			value: checked.map((item: { id: string; industry: string }) => item.industry).join(', ')
		};
				
	} else if (typeof checked === 'string') {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			[optionId]: checked
		};
	} else if (groupId == 'certification') {
		const currentValues = Array.isArray(selectedFilters[groupId]?.value)
			? (selectedFilters[groupId]?.value as string[])
			: [];

		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			value: checked
				? [...currentValues, optionId]
				: currentValues.filter((id) => id !== optionId)
		};
	} else {
		newFilters[groupId] = {
			...((newFilters[groupId] as any) || {}),
			value: checked ? optionId : ''
		};
	}

	Object.keys(newFilters).forEach((key) => {
		const filter = newFilters[key];
		if (!filter) return;

		if (filter.value === null || (Array.isArray(filter.value) && filter.value.length === 0)) {
			delete newFilters[key];
		}

		if (typeof filter.value === 'object' && filter.value !== null) {
			const values = Object.values(filter.value);
			if (values.every((val) => val === '' || val === null)) {
				delete newFilters[key];
			}
		}
	});

	return newFilters;
}