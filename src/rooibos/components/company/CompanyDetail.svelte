<!-- companydetail.svelte -->
<script lang="ts">
	import { MapPin, Briefcase, Microscope, Award, Users, DollarSign } from 'lucide-svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { formatBusinessNumber } from '../common/helper';

	export let company: any;
	export let financialData: any = null;

	const hasBasicInfo = (c: any) =>
		c.business_registration_number ||
		c.corporate_number ||
		c.representative ||
		c.address ||
		c.cri_company_size ||
		c.phone_number ||
		c.establishment_date ||
		c.employee_count ||
		c.fiscal_month ||
		c.main_bank ||
		c.website;

	const hasIndustryInfo = (c: any) => c.industry || c.main_product;

	const hasLabInfo = (c: any) => c.research_info;

	const hasCertificationInfo = (c: any) => c.sme_type;

	const hasVentureInfo = (c: any) => c.venture_confirmation_type || c.venture_valid_from;

	const hasShareholderInfo = (c: any) =>
		c.is_family_shareholder === 'Y' || c.is_non_family_shareholder === 'Y';

	function formatDate(dateStr: any) {
		if (!dateStr) return '';
		return String(dateStr).replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
	}

	$: years =
		financialData && Array.isArray(financialData)
			? [...new Set(financialData.map((d) => String(d.year)))].sort().reverse()
			: [];

	$: if (company && company.master_id) {
		fetchFinancialData(company.master_id);
	}

	async function fetchFinancialData(master_id: string) {
		try {
			const financialResponse = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/corpsearch/${master_id}/financialData`,
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: `Bearer ${localStorage.token}`
					}
				}
			);
			const data = await financialResponse.json();
			financialData = data.financial_data;
		} catch (error) {
			console.error('재무 데이터 로딩 실패:', error);
			financialData = null;
		}
	}
</script>

<div class="company-info-wrapper active flex flex-col w-full overflow-hidden">
	<div class="flex-1 px-4 pb-16">
		<div class="space-y-6 mt-2">
			{#if hasBasicInfo(company)}
				<div id="basic" class="space-y-2 border-gray-100 pb-4 text-gray-900 dark:text-gray-500">
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
						<MapPin size={16} class="text-blue-500" />
						기본 정보
					</h3>
					<div class="space-y-1">
						{#if company.business_registration_number}
							<p class="text-sm flex items-center justify-between">
								<span>사업자 등록 번호</span>
								<span>{formatBusinessNumber(company.business_registration_number)}</span>
							</p>
						{/if}
						{#if company.corporate_number}
							<p class="text-sm flex items-center justify-between">
								<span>법인등록번호</span>
								<span>{company.corporate_number}</span>
							</p>
						{/if}
						{#if company.representative}
							<p class="text-sm flex items-center justify-between">
								<span>대표이사</span>
								<span>
									{company.representative}
									{company.birth_year ? `(${company.birth_year})` : ''}
								</span>
							</p>
						{/if}
						{#if company.address}
							<p class="text-sm flex items-center justify-between">
								<span>주소</span>
								<span>{company.address}</span>
							</p>
						{/if}
						{#if company.cri_company_size}
							<p class="text-sm flex items-center justify-between">
								<span>기업규모</span>
								<span>{company.cri_company_size}</span>
							</p>
						{/if}
						{#if company.phone_number}
							<p class="text-sm flex items-center justify-between">
								<span>전화번호</span>
								<span>{company.phone_number}</span>
							</p>
						{/if}
						{#if company.establishment_date}
							<p class="text-sm flex items-center justify-between">
								<span>설립일</span>
								<span>{formatDate(company.establishment_date)}</span>
							</p>
						{/if}
						{#if company.employee_count}
							<p class="text-sm flex items-center justify-between">
								<span>임직원 수</span>
								<span>{company.employee_count}명</span>
							</p>
						{/if}
						{#if company.fiscal_month}
							<p class="text-sm flex items-center justify-between">
								<span>결산월</span>
								<span>{company.fiscal_month}월</span>
							</p>
						{/if}
						{#if company.main_bank}
							<p class="text-sm flex items-center justify-between">
								<span>주거래은행</span>
								<span>{company.main_bank}</span>
							</p>
						{/if}
						{#if company.website}
							<p class="text-sm flex items-center justify-between">
								<span>웹사이트</span>
								<a
									href={company.website.startsWith('http')
										? company.website
										: `https://${company.website}`}
									target="_blank"
									rel="noopener noreferrer"
									class="text-blue-500 underline"
								>
									{company.website.startsWith('http')
										? company.website
										: `https://${company.website}`}
								</a>
							</p>
						{/if}
					</div>
				</div>
			{/if}

			{#if hasIndustryInfo(company)}
				<div
					id="industry"
					class="space-y-2 border-t border-gray-100 pt-6 text-gray-900 dark:text-gray-400"
				>
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
						<Briefcase size={16} class="text-blue-500" />
						업종 정보
					</h3>
					<div class="space-y-1">
						{#if company.industry}
							<p class="text-sm flex items-center justify-between">
								<span>업종</span>
								<span>{company.industry}</span>
							</p>
						{/if}
						{#if company.main_product}
							<p class="text-sm flex items-center justify-between">
								<span>주요상품</span>
								<span>{company.main_product}</span>
							</p>
						{/if}
					</div>
				</div>
			{/if}

			{#if hasLabInfo(company)}
				<div
					id="lab"
					class="space-y-2 border-t border-gray-100 pt-6 text-gray-900 dark:text-gray-400"
				>
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
						<Microscope size={16} class="text-indigo-500" />
						연구소 정보
					</h3>
					<div class="space-y-1">
						{#if company.research_info}
							{#each company.research_info as info}
								<p class="text-sm flex items-center justify-between">
									<span>구분</span>
									<span>{info.division}</span>
								</p>
								<p class="text-sm flex items-center justify-between">
									<span>연구소명</span>
									<span>{info.lab_name}</span>
								</p>
								<p class="text-sm flex items-center justify-between">
									<span>연구분야</span>
									<span>{info.research_field}</span>
								</p>
								<p class="text-sm flex items-center justify-between">
									<span>최초인정일</span>
									<span>{info.first_approval_date}</span>
								</p>
								<p class="text-sm flex items-center justify-between">
									<span>연구소 위치</span>
									<span>{info.lab_location}</span>
								</p>
							{/each}
						{/if}
					</div>
				</div>
			{/if}

			{#if hasCertificationInfo(company)}
				<div
					id="certification"
					class="space-y-2 border-t border-gray-100 pt-6 text-gray-900 dark:text-gray-400"
				>
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
						<Award size={16} class="text-purple-500" />
						인증 정보
					</h3>
					<div class="space-y-1">
						{#if company.sme_type}
							{#each company.sme_type as sm}
								<p class="text-sm flex items-center justify-between">
									<span>인증 유형</span>
									<span>{sm.sme_type}</span>
								</p>
								<p class="text-sm flex items-center justify-between">
									<span>인증 만료일</span>
									<span>{sm.certificate_expiry_date}</span>
								</p>
							{/each}
						{/if}
					</div>
				</div>
			{/if}

			{#if hasVentureInfo(company)}
				<div
					id="certification"
					class="space-y-2 border-t border-gray-100 pt-6 text-gray-900 dark:text-gray-400"
				>
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
						<Award size={16} class="text-purple-500" />
						벤처기업 정보
					</h3>
					<div class="space-y-1">
						{#if company.venture_confirmation_type}
							<p class="text-sm flex items-center justify-between">
								<span>벤처기업 인증</span>
								<span>{company.venture_confirmation_type}</span>
							</p>
						{/if}
						{#if company.venture_valid_from || company.venture_valid_until || company.confirming_authority || company.new_reconfirmation_code}
							<p class="text-sm flex items-center justify-between">
								<span>벤처 유효기간</span>
								<span>{company.venture_valid_from} ~ {company.venture_valid_until}</span>
							</p>
							<p class="text-sm flex items-center justify-between">
								<span>확인기관</span>
								<span>{company.confirming_authority}</span>
							</p>
							<p class="text-sm flex items-center justify-between">
								<span>재확인코드</span>
								<span>{company.new_reconfirmation_code}</span>
							</p>
						{/if}
					</div>
				</div>
			{/if}

			{#if hasShareholderInfo(company)}
				<div id="shareholders" class="space-y-2 border-t border-gray-100 pt-6">
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
						<Users size={16} class="text-yellow-500" />
						주주 정보
					</h3>
					<div class="space-y-1 text-gray-900 dark:text-gray-400">
						<p class="text-sm flex items-center justify-between">
							<span>가족주주</span>
							<span>{company.is_family_shareholder === 'Y' ? '있음' : '없음'}</span>
						</p>

						<p class="text-sm flex items-center justify-between">
							<span>외부주주</span>
							<span>{company.is_non_family_shareholder === 'Y' ? '있음' : '없음'}</span>
						</p>
					</div>
				</div>
			{/if}

			{#if financialData && Array.isArray(financialData) && financialData.length > 0}
				<div class="space-y-4 border-t border-gray-100 pt-6">
					<!-- 손익계산서 -->
					<div class="space-y-2">
						<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
							<DollarSign size={16} class="text-green-500" />
							재무분석 <span class="inline-block text-xs text-gray-500">단위: 백만원</span>
						</h3>
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b border-gray-300 text-gray-900 dark:text-gray-400">
									<th class="text-left px-2 font-medium py-2">손익계산서</th>
									{#each years as year}
										<th class="w-1/5 text-right px-2 py-2 font-medium whitespace-nowrap"
											>{year}년</th
										>
									{/each}
								</tr>
							</thead>
							<tbody class="text-gray-900 dark:text-gray-500">
								{#each [{ name: '매출액', key: 'revenue' }, { name: '매출원가', key: 'sales_cost' }, { name: '매출총이익', key: 'sales_profit' }, { name: '판매관리비', key: 'sga' }, { name: '영업이익', key: 'operating_income' }, { name: '기타수익', key: 'other_income' }, { name: '기타비용', key: 'other_expenses' }, { name: '세전이익', key: 'pre_tax_income' }, { name: '법인세', key: 'corporate_tax' }, { name: '당기순이익', key: 'net_income' }] as metric}
									<tr class="border-b border-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800">
										<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
										{#each years as year}
											{@const yearData = financialData.find((d) => String(d.year) === year)}
											<td class="w-1/5 text-right px-2 py-2">
												{#if yearData && yearData[metric.key] != null}
													<span
														class="{yearData[metric.key] < 0
															? 'text-red-500'
															: ''} whitespace-nowrap"
													>
														{new Intl.NumberFormat('ko-KR').format(yearData[metric.key])}
													</span>
												{:else}
													-
												{/if}
											</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
					<!-- 재무상태표 -->
					<div class="space-y-2">
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b border-gray-200 text-gray-900 dark:text-gray-400">
									<th class="text-left px-2 font-medium py-2">재무상태표</th>
									{#each years as year}
										<th class="w-1/5 text-right px-2 py-2 font-medium whitespace-nowrap"
											>{year}년</th
										>
									{/each}
								</tr>
							</thead>
							<tbody class="text-gray-900 dark:text-gray-500">
								<!-- 자산 부분 -->
								<tr class="text-gray-900 dark:text-gray-400">
									<td colspan={years.length + 1} class="px-2 py-1 font-semibold">자산</td>
								</tr>
								{#each [
									{ name: '총자산', key: 'recent_total_assets' },
									{ name: '유동자산', key: 'current_assets' }, 
									{ name: '• 당좌자산', key: 'quick_assets' }, 
									{ name: '• 재고자산', key: 'inventory' }, 
									{ name: '비유동자산', key: 'non_current_assets' }, 
									{ name: '• 투자자산', key: 'investment_assets' }, 
									{ name: '• 유형자산', key: 'tangible_assets' }, 
									{ name: '• 무형자산', key: 'intangible_assets' }
								] as metric}
									<tr class="border-b border-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800">
										<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
										{#each years as year}
											{@const yearData = financialData.find((d) => String(d.year) === year)}
											<td class="w-1/5 text-right px-2 py-2">
												{#if yearData && yearData[metric.key] != null}
													<span class="whitespace-nowrap">
														{new Intl.NumberFormat('ko-KR').format(yearData[metric.key])}
													</span>
												{:else}
													-
												{/if}
											</td>
										{/each}
									</tr>
								{/each}
								<!-- 부채와 자본 부분 -->
								<tr class="hover:bg-gray-100 dark:hover:bg-gray-800">
									<td
										colspan={years.length + 1}
										class="px-2 py-1 font-semibold text-gray-900 dark:text-gray-400">부채와 자본</td
									>
								</tr>
								{#each [
									{ name: '유동부채', key: 'current_liabilities' }, 
									{ name: '비유동부채', key: 'non_current_liabilities' }, 
									{ name: '자본금', key: 'capital_stock' }, 
									{ name: '총이익잉여금', key: 'retained_earnings' },
									{ name: '총자본', key: 'recent_total_equity' }
								] as metric}
									<tr class="border-b border-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800">
										<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
										{#each years as year}
											{@const yearData = financialData.find((d) => String(d.year) === year)}
											<td class="w-1/5 text-right px-2 py-2">
												{#if yearData && yearData[metric.key] != null}
													<span class="whitespace-nowrap">
														{new Intl.NumberFormat('ko-KR').format(yearData[metric.key])}
													</span>
												{:else}
													-
												{/if}
											</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
<style>
	.company-info-wrapper p.text-sm.flex.items-center.justify-between {
		display: flex !important;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		margin-left: 1rem;
		margin-right: 1rem;
	}
  </style>
  