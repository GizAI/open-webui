<script context="module" lang="ts">
	declare var naver: any;
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import SearchBar from './SearchBar.svelte';
	import { compayMarkerInfo } from './companymarkerinfo';
	import { filterGroups } from './filterdata';
	import { mobile } from '$lib/stores';
	import { showSidebar, user } from '$lib/stores';
	import SearchCompanyList from './SearchCompanyList.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import CorpInfo from '../corpinfo/CorpInfo.svelte';
	import { OverlappingMarkerSpiderfier } from './marker';

	type MapInstance = {
		map: any;
		marker: any;
		infoWindow: any;
		companyMarkers: any[];
	};

	type Location = {
		lat: number;
		lng: number;
	};

	type UserLocation = {
		lat: number;
		lng: number;
	};

	type SearchResult = {
		smtp_id: string;
		company_name: string;
		address: string;
		latitude: string;
		longitude: string;
		phone_number?: string;
		category?: string[];
		business_registration_number?: string;
		representative?: string;
		birth_date?: string;
		industry?: string;
		establishment_date?: string;
		employee_count?: number;
		recent_sales?: number;
		recent_revenue?: number;
		recent_profit?: number;
		website?: string;
		distance_from_user?: number;
		bookmark_id?: string | null;
		fax_number?: string;
		email?: string;
		company_type?: string;
		founding_date?: string;
		industry_code1?: string;
		industry_code2?: string;
		main_product?: string;
		main_bank?: string;
		main_branch?: string;
		group_name?: string;
		stock_code?: string;
		corporate_number?: string;
		english_name?: string;
		trade_name?: string;
		fiscal_month?: string;
		sales_year?: string;
		profit_year?: string;
		operating_profit_year?: string;
		recent_operating_profit?: number;
		asset_year?: string;
		recent_total_assets?: number;
		debt_year?: string;
		recent_total_debt?: number;
		equity_year?: string;
		recent_total_equity?: number;
		capital_year?: string;
		recent_capital?: number;
		region1?: string;
		region2?: string;
		industry_major?: string;
		industry_middle?: string;
		industry_small?: string;
		certificate_expiry_date?: string;
		sme_type?: string;
		cri_company_size?: string;
		lab_name?: string;
		first_approval_date?: string;
		lab_location?: string;
		research_field?: string;
		division?: string;
		birth_year?: string;
		foundation_year?: string;
		family_shareholder_yn?: string;
		external_shareholder_yn?: string;
		financial_statement_year?: string;
		employees?: number;
		total_assets?: number;
		total_equity?: number;
		sales_amount?: number;
		net_income?: number;
		venture_confirmation_type?: string;
		svcl_region?: string;
		venture_valid_from?: string;
		venture_valid_until?: string;
		confirming_authority?: string;
		new_reconfirmation_code?: string;
	};

	type Filters = {
		radius?: string;
		distance?: string;
		representative?: string;
		gender?: string;
		loan?: string;
		[key: string]: any; // Allow additional keys
	};

	interface CompanyInfo {
		id: string;
		company_id: string;
		company_name: string;
		roadAddress?: string;
		address?: string;
		category?: string[];
		business_registration_number?: number;
		industry?: string;
		representative?: string;
		birth_date?: string;
		establishment_date?: string;
		employee_count?: number;
		phone_number?: string;
		website?: string;
		distance_from_user?: number;
		created_at?: string;
		updated_at?: string;
		files: any[];
		smtp_id: string;
		latitude: string;
		longitude: string;
		bookmark_id?: string | null;
		fax_number?: string;
		email?: string;
		company_type?: string;
		founding_date?: string;
		industry_code1?: string;
		industry_code2?: string;
		main_product?: string;
		main_bank?: string;
		main_branch?: string;
		group_name?: string;
		stock_code?: string;
		corporate_number?: string;
		english_name?: string;
		trade_name?: string;
		fiscal_month?: string;
		region1?: string;
		region2?: string;
		industry_major?: string;
		industry_middle?: string;
		industry_small?: string;
		certificate_expiry_date?: string;
		sme_type?: string;
		cri_company_size?: string;
		lab_name?: string;
		first_approval_date?: string;
		lab_location?: string;
		research_field?: string;
		division?: string;
		birth_year?: string;
		foundation_year?: string;
		family_shareholder_yn?: string;
		external_shareholder_yn?: string;
		financial_statement_year?: string;
		employees?: number;
		venture_confirmation_type?: string;
		svcl_region?: string;
		venture_valid_from?: string;
		venture_valid_until?: string;
		confirming_authority?: string;
		new_reconfirmation_code?: string;
		postal_code?: string;
	}

	let selectedFilters: Filters = {}; // Define selectedFilters with the Filters type

	let mapInstance: MapInstance | null = null;
	let searchResults: SearchResult[] = [];
	let location: Location | null = null;
	let error: string | null = null;
	let loading = true;
	let script: HTMLScriptElement;
	let searchValue: string = '';
	let showSearchList = false;
	let isListIconVisible = true;
	let activeFilterGroup: string | null = null;
	let userLocation: UserLocation | null = null;
	let showCompanyInfo = false;
	let zoom = 18;
	let isFullscreen = false;
	let companyInfo: CompanyInfo = {
		id: '',
		company_id: '',
		company_name: '',
		files: [],
		smtp_id: '',
		latitude: '',
		longitude: ''
	};

	const handleSearch = async (searchValue: string, filters: any) => {
		console.log('Searching for:', searchValue, 'with filters:', filters);

		showSearchList = false;
		activeFilterGroup = null;
		isListIconVisible = true;

		try {
			const currentUser = get(user);
			const queryParams = new URLSearchParams({
				query: searchValue,
				user_id: currentUser?.id ? currentUser.id : '',
				latitude: location ? location.lat.toString() : '',
				longitude: location ? location.lng.toString() : '',
				userLatitude: location?.lat?.toString() || '',
				userLongitude: location?.lng?.toString() || '',
				filters: JSON.stringify(filters)
			});

			const response = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/corpsearch/?${queryParams.toString()}`,
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: `Bearer ${localStorage.token}`
					}
				}
			);

			if (!response.ok) {
				throw new Error('검색 요청 실패');
			}

			const data = await response.json();

			searchResults = data.data;
			showSearchList = true;

			if (!searchResults.length) {
				if (mapInstance?.companyMarkers) {
					mapInstance.companyMarkers.forEach((marker) => marker.setMap(null));
					mapInstance.companyMarkers = [];
				}
				return;
			}

			if (!mapInstance) return;

			if (mapInstance?.companyMarkers) {
				mapInstance.companyMarkers.forEach((marker) => marker.setMap(null));
				mapInstance.companyMarkers = [];
			}

			// if (mapInstance?.marker) {
			//     mapInstance.marker.setMap(null);
			// }

			const firstPoint = new naver.maps.LatLng(location?.lat, location?.lng);

			mapInstance.map.setCenter(firstPoint);
			mapInstance.map.setZoom(zoom);

			const spiderfier = new OverlappingMarkerSpiderfier(mapInstance.map);

			searchResults.forEach((result, index) => {
				const point = new naver.maps.LatLng(
					parseFloat(result.latitude),
					parseFloat(result.longitude)
				);

				if (mapInstance) {
					const marker = new naver.maps.Marker({
						position: point,
						map: mapInstance.map,
						title: result.company_name,
						zIndex: 100,
						icon: {
							content: getMarkerContent(result),
							anchor: new naver.maps.Point(50, 30) // 앵커 포인트를 아래로 조정
						}
					});

					naver.maps.Event.addListener(marker, 'mouseover', function () {
						marker.setZIndex(200);
					});

					naver.maps.Event.addListener(marker, 'mouseout', () => {
						marker.setZIndex(100);
					});

					naver.maps.Event.addListener(marker, 'click', () => {
						companyInfo = result;
						showCompanyInfo = true;
						showSearchList = false;
						activeFilterGroup = null;
					});
					spiderfier.addMarker(marker);
					mapInstance.companyMarkers.push(marker);
				}
			});
		} catch (error) {
			console.error('검색 중 오류가 발생했습니다:', error);
		}
	};

	const handleReset = () => {
		selectedFilters = {};
		handleSearch('', selectedFilters);
	};

	const handleApply = () => {
		handleSearch(searchValue, selectedFilters);
	};

	const initializeMap = (position: any) => {
		const mapContainer = document.getElementById('map');

		handleSearch('', selectedFilters);

		if (!mapContainer) {
			console.error('Map container not found');
			return;
		}
		const mapOptions = {
			center: new naver.maps.LatLng(position.lat, position.lng),
			zoom: zoom
		};

		const map = new naver.maps.Map(mapContainer, mapOptions);
		const marker = new naver.maps.Marker({
			position: new naver.maps.LatLng(position.lat, position.lng),
			map: map
		});

		mapInstance = { map, marker, infoWindow: null, companyMarkers: [] };
		loading = false;

		naver.maps.Event.addListener(map, 'click', (e: any) => {
			if (location) {
				location.lat = e.coord._lat;
				location.lng = e.coord._lng;
				showCompanyInfo = false;
			}
			activeFilterGroup = null;
		});

		naver.maps.Event.addListener(map, 'dragend', (e: any) => {
			if (location) {
				showCompanyInfo = false;
				const center = map.getCenter();
				location.lat = center.lat();
				location.lng = center.lng();
				handleSearch('', selectedFilters);
				activeFilterGroup = null;
			}
		});

		naver.maps.Event.addListener(map, 'zoom_changed', () => {
			zoom = map.getZoom(); // 줌 변경 시 현재 줌 값 저장
			console.log('zoom:', zoom);
		});
	};

	const moveToCurrentLocation = () => {
		if (!location || !mapInstance) {
			alert('현재 위치를 가져올 수 없습니다.');
			return;
		}

		if (userLocation) {
			location.lat = userLocation.lat;
			location.lng = userLocation.lng;
			const currentLocation = new naver.maps.LatLng(userLocation.lat, userLocation.lng);
			mapInstance.map.setCenter(currentLocation);

			if (mapInstance.marker) {
				mapInstance.marker.setPosition(currentLocation);
				mapInstance.marker.setMap(mapInstance.map);
			} else {
				mapInstance.marker = new naver.maps.Marker({
					position: currentLocation,
					map: mapInstance.map
				});
			}
			handleSearch('', selectedFilters);
		}
	};

	const handleSearchResultClick = (result: SearchResult) => {
		if (!mapInstance) return;

		const point = new naver.maps.LatLng(parseFloat(result.latitude), parseFloat(result.longitude));

		mapInstance?.map.setCenter(point);
		mapInstance.map.setZoom(zoom);

		const spiderfier = new OverlappingMarkerSpiderfier(mapInstance.map);

		if (mapInstance) {
			const marker = new naver.maps.Marker({
				position: point,
				map: mapInstance.map,
				title: result.company_name,
				zIndex: 100,
				icon: {
					content: getMarkerContent(result),
					anchor: new naver.maps.Point(50, 30) // 앵커 포인트를 아래로 조정
				}
			});

			// 마우스 오버 시 최상단으로 표시
			naver.maps.Event.addListener(marker, 'mouseover', () => {
				marker.setZIndex(200); // 다른 마커보다 높은 zIndex 설정
			});

			// 마우스 아웃 시 기본 zIndex로 복귀
			naver.maps.Event.addListener(marker, 'mouseout', () => {
				marker.setZIndex(100);
			});

			naver.maps.Event.addListener(marker, 'click', () => {
				companyInfo = result;
				showCompanyInfo = true;
			});
			spiderfier.addMarker(marker);
			mapInstance.companyMarkers.push(marker);
		}

		showSearchList = false;
		handleSearchListChange(false);
	};

	const handleSearchAddressListClick = (searchAddressList: SearchResult[]) => {
		if (!mapInstance) return;

		const firstResult = searchAddressList[0];
		const point = new naver.maps.LatLng(
			parseFloat(firstResult.latitude),
			parseFloat(firstResult.longitude)
		);

		mapInstance?.map.setCenter(point);
		mapInstance.map.setZoom(zoom);

		const spiderfier = new OverlappingMarkerSpiderfier(mapInstance.map);

		searchAddressList.forEach((result, index) => {
			const point = new naver.maps.LatLng(
				parseFloat(result.latitude),
				parseFloat(result.longitude)
			);

			if (mapInstance) {
				const marker = new naver.maps.Marker({
					position: point,
					map: mapInstance.map,
					title: result.company_name,
					zIndex: 100,
					icon: {
						content: getMarkerContent(result),
						anchor: new naver.maps.Point(50, 30) // 앵커 포인트를 아래로 조정
					}
				});

				naver.maps.Event.addListener(marker, 'mouseover', function () {
					marker.setZIndex(200);
				});

				naver.maps.Event.addListener(marker, 'mouseout', () => {
					marker.setZIndex(100);
				});

				naver.maps.Event.addListener(marker, 'click', () => {
					companyInfo = result;
					showCompanyInfo = true;
					showSearchList = false;
					activeFilterGroup = null;
				});
				spiderfier.addMarker(marker);
				mapInstance.companyMarkers.push(marker);
			}
		});

		showSearchList = false;
		handleSearchListChange(false);
	};

	const handleSearchListChange = (newValue: boolean) => {
		showSearchList = newValue;
	};

	onMount(() => {
		const initialize = async () => {
			try {
				const options = {
					enableHighAccuracy: true,
					maximumAge: 0,
					timeout: 5000
				};

				const position = await new Promise<GeolocationPosition>((resolve, reject) => {
					navigator.geolocation.getCurrentPosition(resolve, reject, options);
				});

				location = {
					lat: position.coords.latitude,
					lng: position.coords.longitude
				};

				userLocation = {
					lat: position.coords.latitude,
					lng: position.coords.longitude
				};

				script = document.createElement('script');
				script.src = `https://openapi.map.naver.com/openapi/v3/maps.js?ncpClientId=t80s8o2xsl&submodules=geocoder`;
				script.async = true;

				script.onload = () => {
					initializeMap(location);
				};

				document.body.appendChild(script);
			} catch (err) {
				const errorMessage = (err as Error).message;
				error = errorMessage;
				loading = false;
			}
		};

		initialize();

		return () => {
			if (document.body.contains(script)) {
				document.body.removeChild(script);
			}
		};
	});

	// 1. 새 헬퍼 함수를 추가합니다.
	function getMarkerContent(result: SearchResult): string {
		return `
    <div class="marker-content" style="
        position: relative;
        padding: 8px;
        background: white;
        border: 1px solid #888;
        border-radius: 6px;
        text-align: center;
        min-width: 120px;
        font-size: 12px;
        transition: all 0.2s;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="
            position: absolute;
            bottom: -8px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-top: 8px solid white;
            filter: drop-shadow(0 2px 1px rgba(0,0,0,0.1));
        "></div>
        <div style="
            position: absolute;
            bottom: -7px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-top: 8px solid #888;
            z-index: -1;
        "></div>
        <div style="font-weight: bold;">${result.company_name}(${result.business_registration_number})</div>
        <div style="font-size: 11px; color: #666; margin-top: 2px;">
            ${result.representative || '대표자 미상'}
        </div>
    </div>
  `;
	}

	function onFilterChange(groupId: string, optionId: string, checked: boolean | string) {
		const group = filterGroups.find((g) => g.id === groupId);
		if (!group) return;

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
		} else if (groupId === 'representative_age') {
			newFilters[groupId] = {
				...((newFilters[groupId] as any) || {}),
				value: checked
			};
		} else if (groupId === 'establishment_year') {
			newFilters[groupId] = {
				...((newFilters[groupId] as any) || {}),
				value: checked
			};
		} else if (
			['employee_count', 'sales', 'profit', 'net_profit', 'unallocated_profit'].includes(groupId) &&
			typeof checked === 'object' &&
			checked !== null
		) {
			newFilters[groupId] = {
				...((newFilters[groupId] as any) || {}),
				...checked
			};
		} else if (typeof checked === 'string') {
			newFilters[groupId] = {
				...((newFilters[groupId] as any) || {}),
				[optionId]: checked
			};
		} else if (group.isMulti) {
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

		selectedFilters = newFilters;

		const excludedGroupIds = [
			'employee_count',
			'sales',
			'profit',
			'net_profit',
			'unallocated_profit',
			'establishment_year',
			'representative_age'
		];

		if (!excludedGroupIds.includes(groupId)) {
			handleSearch('', selectedFilters);
		}

		return newFilters;
	}

	function closeCompanyInfo() {
		showCompanyInfo = false;
		showSearchList = true;
	}

	const handleResultClick = (result: SearchResult) => {
		return;
		if (!mapInstance) return;

		const point = new naver.maps.LatLng(parseFloat(result.latitude), parseFloat(result.longitude));

		mapInstance.map.setCenter(point);
		mapInstance.map.setZoom(zoom);
		// mapInstance.infoWindow.close();
		// mapInstance.infoWindow.setContent(compayMarkerInfo(result));

		const marker = mapInstance.companyMarkers.find((m) => m.getTitle() === result.company_name);

		if (marker) {
			mapInstance.infoWindow.open(mapInstance.map, marker);
		}

		showSearchList = false;
		isListIconVisible = !isListIconVisible;
		handleSearchListChange(false);
	};
</script>

{#if !($showSidebar && $mobile) && (!showCompanyInfo || !isFullscreen)}
	<div class="search-bar-wrapper w-full" class:sidebar-visible={$showSidebar}>
		<SearchBar
			onSearch={handleSearch}
			onReset={handleReset}
			onApply={handleApply}
			{searchValue}
			{activeFilterGroup}
			{onFilterChange}
			{selectedFilters}
			on:showCompanyInfo={(e) => (showCompanyInfo = e.detail)}
			on:filterGroupChange={(e) => (activeFilterGroup = e.detail)}
			on:searchResultClick={(e) => handleSearchResultClick(e.detail)}
			on:addressResultClick={(e) => handleSearchAddressListClick(e.detail)}
		/>
	</div>
{/if}

{#if false && searchResults.length > 1 && showSearchList && !($mobile && $showSidebar)}
	<div class="company-list-wrapper w-full" class:sidebar-visible={$showSidebar}>
		<SearchCompanyList
			{searchResults}
			onResultClick={handleResultClick}
			bind:isFullscreen
			onClose={closeCompanyInfo}
		/>
	</div>
{/if}

{#if showCompanyInfo && companyInfo}
	<div class:sidebar-visible={$showSidebar}>
		<CorpInfo {companyInfo} onClose={closeCompanyInfo} bind:isFullscreen />
	</div>
{/if}

{#if loading}
	<div class="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
		<p>지도를 불러오는 중...</p>
	</div>
{/if}

{#if error}
	<div class="fixed inset-0 flex items-center justify-center">
		<p class="text-red-500">
			{error === 'User denied Geolocation'
				? '위치 접근을 허용해주세요.'
				: '위치를 가져오는데 실패했습니다.'}
		</p>
	</div>
{/if}

<div id="map" class="w-full h-full relative" />

<button
	on:click={moveToCurrentLocation}
	class="absolute bottom-20 right-5 bg-transparent border rounded-full w-12 h-12 flex items-center justify-center shadow-lg z-30 hover:bg-gray-100"
>
	<svg
		xmlns="http://www.w3.org/2000/svg"
		width="24"
		height="24"
		fill="none"
		viewBox="0 0 24 24"
		stroke="#374151"
		stroke-width="1"
	>
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="M12 2v20m-10-10h20M12 4.5c4.97 0 9 4.03 9 9s-4.03 9-9 9-9-4.03-9-9 4.03-9 9-9z"
		/>
	</svg>
</button>

<!-- SearchBar.svelte 스타일 수정 -->
<style>
	.search-bar-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		width: 100%;
		z-index: 50;
		transition: margin-left 0.3s ease-in-out;
		box-sizing: border-box;
		background-color: white;
		border-bottom: 1px solid #e5e7eb;
	}

	.search-bar-wrapper.sidebar-visible {
		margin-left: 260px; /* left 속성 대신 margin-left 사용 */
		width: calc(100% - 256px);
	}

	@media (max-width: 768px) {
		.search-bar-wrapper.sidebar-visible {
			margin-left: 0;
			width: 100%;
		}
	}

	.company-list-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		width: 100%;
		z-index: 50;
		transition: margin-left 0.3s ease-in-out;
		box-sizing: border-box;
		background-color: white;
		border-bottom: 1px solid #e5e7eb;
	}

	.company-list-wrapper.sidebar-visible {
		margin-left: 256px; /* left 속성 대신 margin-left 사용 */
		width: calc(100% - 256px);
	}

	#map {
		position: relative;
	}
</style>
