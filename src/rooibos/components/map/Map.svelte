<script context="module" lang="ts">
	declare var naver: any;
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { excludedGroupIds, onFilterChange } from '../corpsearch/filterdata';
	import { mobile } from '$lib/stores';
	import { showSidebar, user, WEBUI_NAME } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { darkStyle, getMarkerContent } from './marker';
	import SearchBar from '../corpsearch/SearchBar.svelte';
	import CompanyList from '../company/CompanyList.svelte';
	import CompanyInfo from '../company/CompanyInfo.svelte';

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
		master_id: string;
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
		bookmark_id?: string;
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
		sme_type?: { sme_type: string; certificate_expiry_date: string }[];
		research_info?: {
			lab_name: string;
			lab_location: string;
			first_approval_date: string;
			research_field: string;
			division: string;
		}[];
		birth_year?: string;
		foundation_year?: string;
		is_family_shareholder?: string;
		is_non_family_shareholder?: string;
		financial_statement_year?: string;
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
		[key: string]: any;
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
		master_id: string;
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
		sme_type?: { sme_type: string; certificate_expiry_date: string }[];
		research_info?: {
			lab_name: string;
			lab_location: string;
			first_approval_date: string;
			research_field: string;
			division: string;
		}[];
		birth_year?: string;
		foundation_year?: string;
		is_family_shareholder?: string;
		is_non_family_shareholder?: string;
		financial_statement_year?: string;
		venture_confirmation_type?: string;
		svcl_region?: string;
		venture_valid_from?: string;
		venture_valid_until?: string;
		confirming_authority?: string;
		new_reconfirmation_code?: string;
		postal_code?: string;
	}

	let selectedFilters: Filters = {};
	let selectedMarker: any = null;
	let mapInstance: MapInstance | null = null;
	let searchResults: SearchResult[] = [];
	let companyList: SearchResult[] = [];
	let location: Location | null = null;
	let error: string | null = null;
	let loading = true;
	let naverScript: HTMLScriptElement;
	let searchValue: string = '';
	let resultViewMode = 'map';
	let isListIconVisible = true;
	let activeFilterGroup: string | null = null;
	let userLocation: UserLocation | null = null;
	let showCompanyInfo = false;
	let zoom = 18;
	let isFullscreen = false;
	let markerClustering: any;
	let companyInfo: CompanyInfo = {
		id: '',
		company_id: '',
		company_name: '',
		files: [],
		master_id: '',
		latitude: '',
		longitude: ''
	};

	function clearMarkers() {
		if (mapInstance?.companyMarkers) {
			mapInstance.companyMarkers.forEach((marker) => marker.setMap(null));
			mapInstance.companyMarkers = [];
		}
		if (markerClustering) {
			markerClustering.clearMarkers();
		}
	}

	function createLatLng(lat: string | number, lng: string | number) {
		const latitude = typeof lat === 'string' ? parseFloat(lat) : lat;
		const longitude = typeof lng === 'string' ? parseFloat(lng) : lng;
		return new naver.maps.LatLng(latitude, longitude);
	}

	function updateSelectedMarker(newMarker: any, result: SearchResult, zIndex: number = 300) {
		if (selectedMarker && selectedMarker !== newMarker) {
			selectedMarker.setIcon({
				content: getMarkerContent(selectedMarker.company_info, false),
				anchor: new naver.maps.Point(50, 30)
			});
			selectedMarker.setZIndex(100);
		}
		selectedMarker = newMarker;
		selectedMarker.setIcon({
			content: getMarkerContent(result, true),
			anchor: new naver.maps.Point(50, 30)
		});
		selectedMarker.setZIndex(zIndex);
	}

	function registerMapEvents(map: any) {
		naver.maps.Event.addListener(map, 'click', (e: any) => {
			if (location) {
				location.lat = e.coord._lat;
				location.lng = e.coord._lng;
				showCompanyInfo = false;
			}

			if (selectedMarker) {
				selectedMarker.setIcon({
					content: getMarkerContent(selectedMarker.company_info),
					anchor: new naver.maps.Point(50, 30)
				});
				selectedMarker = null;
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
			zoom = map.getZoom();
			console.log('zoom:', zoom);
		});
	}

	function loadNaverMapScript(): Promise<void> {
		return new Promise((resolve, reject) => {
			naverScript = document.createElement('script');
			naverScript.src = `https://openapi.map.naver.com/openapi/v3/maps.js?ncpClientId=t80s8o2xsl&submodules=geocoder`;
			naverScript.async = true;
			naverScript.onload = () => resolve();
			naverScript.onerror = (err) => reject(err);
			document.body.appendChild(naverScript);
		});
	}

	function createCompanyMarker(
		result: SearchResult,
		selectedZIndex: number = 300,
		autoSelect: boolean = false
	): any {
		const point = createLatLng(result.latitude, result.longitude);
		const marker = new naver.maps.Marker({
			position: point,
			map: mapInstance?.map,
			title: result.company_name,
			zIndex: 100,
			icon: {
				content: getMarkerContent(result),
				anchor: new naver.maps.Point(50, 30)
			}
		});

		marker.company_info = result;
		marker.company_name = result.company_name;
		marker.business_registration_number = result.business_registration_number;
		marker.representative = result.representative;

		naver.maps.Event.addListener(marker, 'mouseover', () => {
			marker.setZIndex(200);
		});
		naver.maps.Event.addListener(marker, 'mouseout', () => {
			if (selectedMarker !== marker) {
				marker.setZIndex(100);
			}
		});
		naver.maps.Event.addListener(marker, 'click', () => {
			updateSelectedMarker(marker, result, selectedZIndex);
			companyInfo = result;
			showCompanyInfo = true;
			activeFilterGroup = null;
			if ($mobile) {
				// Immediately switch to fullscreen on mobile
				isFullscreen = true;
			}
		});

		if (autoSelect) {
			naver.maps.Event.trigger(marker, 'click');
		}

		return marker;
	}

	async function fetchSearchResults(searchValue: string, filters: any): Promise<SearchResult[]> {
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

			return data.data;
		} catch (error) {
			console.error('서버 통신 중 오류 발생:', error);
			throw error;
		}
	}

	const handleSearch = async (searchValue: string, filters: any) => {
		console.log('Searching for:', searchValue, 'with filters:', filters);
		activeFilterGroup = null;
		isListIconVisible = true;

		try {
			searchResults = await fetchSearchResults(searchValue, filters);

			if (!searchResults.length) {
				clearMarkers();
				return;
			}

			if (!mapInstance) return;

			clearMarkers();

			const firstPoint = createLatLng(location?.lat, location?.lng);
			mapInstance.map.setCenter(firstPoint);
			mapInstance.map.setZoom(zoom);

			searchResults.forEach((result) => {
				if (mapInstance) {
					const marker = createCompanyMarker(result, 300, false);
					markerClustering.addMarker(marker);
					mapInstance.companyMarkers.push(marker);
				}
			});
		} catch (error) {
			console.error('검색 중 오류가 발생했습니다:', error);
		}
	};

	const handleReset = () => {
		selectedFilters = {
			radius: { checked: true, value: '200' }
		};
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
			center: createLatLng(position.lat, position.lng),
			zoom: zoom
			// styles: darkStyle,
			// mapTypeControl: true,
			// scaleControl: false,
			// logoControl: false,
			// mapDataControl: false
		};

		const map = new naver.maps.Map(mapContainer, mapOptions);
		const marker = new naver.maps.Marker({
			position: createLatLng(position.lat, position.lng),
			map: map
		});

		mapInstance = { map, marker, infoWindow: null, companyMarkers: [] };
		loading = false;

		registerMapEvents(map);
	};

	const moveToCurrentLocation = () => {
		if (!location || !mapInstance) {
			alert('현재 위치를 가져올 수 없습니다.');
			return;
		}

		if (userLocation) {
			location.lat = userLocation.lat;
			location.lng = userLocation.lng;
			const currentLocation = createLatLng(userLocation.lat, userLocation.lng);
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

	const handleSearchResults = (results: SearchResult | SearchResult[]) => {
		if (!mapInstance) return;

		const resultArray = Array.isArray(results) ? results : [results];
		const firstResult = resultArray[0];
		const point = createLatLng(firstResult.latitude, firstResult.longitude);

		mapInstance.map.setCenter(point);
		mapInstance.map.setZoom(zoom);

		resultArray.forEach((result) => {
			const marker = createCompanyMarker(result, 300, false);
			markerClustering.addMarker(marker);
			mapInstance.companyMarkers.push(marker);
		});

		searchResults = resultArray;
	};

	const handleShowCompanyListClick = (viewMode: any) => {
		resultViewMode = viewMode;
		companyList = searchResults;

		if (resultViewMode != 'map') showCompanyInfo = false;
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

				await loadNaverMapScript();
				initializeMap(location);

				const module = await import('./MarkerClustering');
				const MarkerClustering = module.default;
				markerClustering = new MarkerClustering({
					map: mapInstance.map,
					gridSize: 60,
					maxZoom: zoom + 1,
					disableClickZoom: false
				});

				handleSearch('', selectedFilters);
			} catch (err) {
				const errorMessage = (err as Error).message;
				error = errorMessage;
				loading = false;
			}
		};

		initialize();

		window.addEventListener('clusterClick', (e: CustomEvent) => {
			companyList = e.detail.markers.map((marker) => marker.company_info);
			resultViewMode = 'list';
			showCompanyInfo = false;
		});

		return () => {
			if (document.body.contains(naverScript)) {
				document.body.removeChild(naverScript);
			}
		};
	});

	async function filterChange(groupId: string, optionId: string, checked: boolean | string) {
		selectedFilters = await onFilterChange(selectedFilters, groupId, optionId, checked);

		if (!excludedGroupIds.includes(groupId)) {
			handleSearch('', selectedFilters);
		}
	}

	function closeCompanyInfo() {
		showCompanyInfo = false;
		resultViewMode = 'map';

		if (selectedMarker) {
			selectedMarker.setIcon({
				content: getMarkerContent(selectedMarker.company_info),
				anchor: new naver.maps.Point(50, 30)
			});
			selectedMarker = null;
		}
	}
</script>

<svelte:head>
	<title>
		기업찾기 | {$WEBUI_NAME}
	</title>
</svelte:head>

{#if !($showSidebar && $mobile)}
	<div class="search-bar-wrapper w-full" class:sidebar-visible={$showSidebar}>
		<SearchBar
			onSearch={handleSearch}
			onReset={handleReset}
			onApply={handleApply}
			searchCompanyResults={searchResults}
			{searchValue}
			{activeFilterGroup}
			{filterChange}
			{selectedFilters}
			{resultViewMode}
			currentLocation={location}
			on:showCompanyInfo={(e) => (showCompanyInfo = e.detail)}
			on:filterGroupChange={(e) => (activeFilterGroup = e.detail)}
			on:searchResultClick={(e) => handleSearchResults(e.detail)}
			on:addressResultClick={(e) => handleSearchResults(e.detail)}
			on:showCompanyListClick={(e) => handleShowCompanyListClick(e.detail)}
		/>
	</div>
{/if}

{#if resultViewMode != 'map' && !($showSidebar && $mobile)}
	<div class="company-list-wrapper w-full" class:sidebar-visible={$showSidebar}>
		<CompanyList {companyList} />
	</div>
{/if}

{#if showCompanyInfo && companyInfo && !($showSidebar && $mobile)}
	<div class="company-info-container" class:sidebar-visible={$showSidebar}>
		<CompanyInfo {companyInfo} onClose={closeCompanyInfo} {isFullscreen} />
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
	class="absolute bottom-10 right-5 bg-transparent border rounded-full w-12 h-12 flex items-center justify-center shadow-lg z-30 hover:bg-gray-100"
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

<style>
	.search-bar-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		z-index: 50; /* z-index 높임 */
		transition: transform 0.3s ease-in-out;
		box-sizing: border-box;
		background-color: white;
		border-bottom: 2px solid #e5e7eb;
	}

	.search-bar-wrapper.sidebar-visible {
		margin-left: 260px;
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
	}

	.company-list-wrapper.sidebar-visible {
		margin-left: 256px;
		width: calc(100% - 256px);
	}

	.company-info-container {
		position: fixed;
		top: 0;
		right: 0;
		width: 30%;
		height: 100%;
		z-index: 49;
		transition: margin-left 0.3s ease-in-out;
		padding-top: 80px; /* 검색 바 높이 + 더 큰 여유 공간 */
	}

	.company-info-container.sidebar-visible {
		width: calc(30% - 0px);
	}

	#map {
		position: relative;
	}
</style>
