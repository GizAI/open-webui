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
	let isIPadMiniDevice = false;
	let companyInfo: CompanyInfo = {
		id: '',
		company_id: '',
		company_name: '',
		files: [],
		master_id: '',
		latitude: '',
		longitude: ''
	};
	// 기본 위치 정보 (서울시청)
	const DEFAULT_LOCATION = {
		lat: 37.5666805,
		lng: 126.9784147,
		name: '서울시청'
	};

	$: if (error !== null) {
		// 오류가 있더라도 지도 뷰를 유지하기 위해 주석 처리
		// resultViewMode = 'list';
		companyList = searchResults;
	}

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
			companyInfo = {
				...result,
				id: result.master_id || '',
				company_id: result.master_id || '',
				files: [],
				business_registration_number: result.business_registration_number ? Number(result.business_registration_number) : undefined
			};
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
		
		// 지도 뷰를 기본으로 설정
		resultViewMode = 'map';

		try {
			searchResults = await fetchSearchResults(searchValue, filters);

			if (!searchResults.length) {
				clearMarkers();
				return;
			}

			if (!mapInstance) return;

			clearMarkers();

			const firstPoint = createLatLng(location?.lat || 0, location?.lng || 0);
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
		try {
			selectedFilters = {};
			// 반경 필터 기본값 설정
			filterChange('radius', '200', '200');
			// 검색 실행
			handleSearch('', selectedFilters);
		} catch (error) {
			console.error('초기화 중 오류가 발생했습니다:', error);
			// 에러 발생 시 알림 표시
			if (error instanceof Error) {
				alert(`초기화 오류: ${error.message}`);
			} else {
				alert('초기화 중 오류가 발생했습니다.');
			}
		}
	};

	const handleApply = () => {
		handleSearch(searchValue, selectedFilters);
	};

	function initializeMap(position: any) {
		const mapContainer = document.getElementById('map');

		// 항상 지도 뷰로 초기화
		resultViewMode = 'map';
		
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

		// 기본 위치를 사용하는 경우 라벨 표시
		if (position.name && position.name === DEFAULT_LOCATION.name) {
			new naver.maps.InfoWindow({
				content: `<div style="padding: 10px; text-align: center;"><strong>현재 위치:</strong> ${position.name}<br><span style="font-size: 12px; color: #666;">실제 위치를 가져올 수 없어 기본 위치를 사용합니다.</span></div>`,
				maxWidth: 300,
				backgroundColor: "#fff",
				borderColor: "#ccc",
				borderWidth: 2,
				anchorSize: new naver.maps.Size(10, 10),
				anchorSkew: true,
				anchorColor: "#fff",
				pixelOffset: new naver.maps.Point(10, -5)
			}).open(map, marker);
		}

		mapInstance = { map, marker, infoWindow: null, companyMarkers: [] };
		loading = false;

		registerMapEvents(map);
	};

	const moveToCurrentLocation = () => {
		if (!mapInstance) {
			alert('지도를 사용할 수 없습니다.');
			return;
		}

		if (userLocation) {
			location = {
				lat: userLocation.lat,
				lng: userLocation.lng
			};
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
		} else {
			alert('현재 위치를 가져올 수 없습니다.');
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
			if (mapInstance) {
				const marker = createCompanyMarker(result, 300, false);
				markerClustering.addMarker(marker);
				mapInstance.companyMarkers.push(marker);
			}
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
				// iPad Mini 감지
				isIPadMiniDevice = detectIPadMini();
				
				if (isIPadMiniDevice && showCompanyInfo) {
					isFullscreen = true;
				}
				
				const options = {
					enableHighAccuracy: true,
					maximumAge: 0,
					timeout: 5000
				};

				try {
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
				} catch (geoError) {
					console.error('위치 정보를 가져오는데 실패했습니다:', geoError);
					error = `위치 정보를 가져오는데 실패했습니다: ${(geoError as Error).message}`;
					
					// 기본 위치 사용
					location = { ...DEFAULT_LOCATION };
					
					// 오류가 있어도 지도 뷰를 유지
					resultViewMode = 'map';
				}

				await loadNaverMapScript();
				initializeMap(location || DEFAULT_LOCATION);

				const module = await import('./MarkerClustering');
				const MarkerClustering = module.default;
				
				// mapInstance가 null이 아닌지 확인 후 markerClustering 초기화
				if (mapInstance) {
					markerClustering = new MarkerClustering({
						map: mapInstance.map,
						gridSize: 60,
						maxZoom: zoom + 1,
						disableClickZoom: false
					});
				}

				handleSearch('', selectedFilters);
				
				// 지도 뷰로 강제 설정
				resultViewMode = 'map';
				
				// 화면 크기 변화 감지
				window.addEventListener('resize', () => {
					// 아이패드 미니 감지 업데이트
					isIPadMiniDevice = detectIPadMini();
					
					// 아이패드 미니에서 전체 화면 모드로 자동 전환
					if (isIPadMiniDevice && showCompanyInfo) {
						isFullscreen = true;
					}
				});
			} catch (err) {
				const errorMessage = (err as Error).message;
				error = errorMessage;
				
				// 오류가 발생해도 기본 위치로 지도 초기화 시도
				try {
					await loadNaverMapScript();
					initializeMap(DEFAULT_LOCATION);
					
					const module = await import('./MarkerClustering');
					const MarkerClustering = module.default;
					
					if (mapInstance) {
						markerClustering = new MarkerClustering({
							map: mapInstance.map,
							gridSize: 60,
							maxZoom: zoom + 1,
							disableClickZoom: false
						});
						
						handleSearch('', selectedFilters);
						
						// 지도 뷰로 강제 설정
						resultViewMode = 'map';
					}
				} catch (mapErr) {
					console.error('지도 초기화 실패:', mapErr);
					// 지도 초기화도 실패하면 목록 뷰로 전환
					resultViewMode = 'list';
				}
			} finally {
				loading = false;
			}
		};

		initialize();

		window.addEventListener('clusterClick', (e: any) => {
			companyList = e.detail.markers.map((marker: any) => marker.company_info);
			// 클러스터 클릭시 목록 보기로 전환
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

	function detectIPadMini() {
		if (typeof window === 'undefined') return false;
		
		// iPad Mini 감지 (약 768 x 1024, iPad Mini 6 기준)
		const userAgent = navigator.userAgent.toLowerCase();
		const isIPad = /ipad/.test(userAgent);
		const isTablet = isIPad || 
			(/tablet/.test(userAgent) && !/android/.test(userAgent)) || 
			((/iphone|ipod/.test(userAgent) || /android/.test(userAgent)) && 
			window.innerWidth >= 750 && window.innerWidth <= 850);

		// iPad Mini의 화면 크기를 고려 (가로/세로 모두 지원)
		return isTablet && 
			((window.innerWidth >= 750 && window.innerWidth <= 850) || 
			(window.innerHeight >= 750 && window.innerHeight <= 850));
	}

	function isIPadMini() {
		return isIPadMiniDevice;
	}
</script>

<svelte:head>
	<title>
		기업찾기 | {$WEBUI_NAME}
	</title>
</svelte:head>

{#if !($showSidebar && $mobile) && !($mobile && showCompanyInfo && isFullscreen) && !(showCompanyInfo && isIPadMini())}
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

{#if showCompanyInfo && companyInfo}
	<div 
		class="company-info-container" 
		class:sidebar-visible={$showSidebar} 
		class:ipad-mini-fullscreen={isIPadMini()}
	>
		<CompanyInfo {companyInfo} onClose={closeCompanyInfo} isFullscreen={isIPadMini() ? true : $mobile} />
	</div>
{/if}

{#if loading}
	<div class="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
		<p>지도를 불러오는 중...</p>
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

	@media (max-width: 760px) and (max-device-width: 767px) {
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
		z-index: 45;
		transition: margin-left 0.3s ease-in-out;
		padding-top: 80px; /* 검색 바 높이 + 더 큰 여유 공간 */
	}

	.company-info-container.sidebar-visible {
		width: calc(30% - 0px);
	}

	/* 아이패드 미니 전용 스타일 - 다른 기기에는 적용되지 않음 */
	.company-info-container.ipad-mini-fullscreen {
		width: 100%;
		left: 0;
		right: 0;
		z-index: 60;
		top: 0;
		padding-top: 0;
	}

	/* 모바일 전용 스타일 */
	@media (max-width: 760px) {
		.company-info-container {
			width: 100%;
			left: 0;
			right: 0;
		}
		
		.company-info-container.sidebar-visible {
			width: 100%;
			margin-left: 0;
		}
	}

	#map {
		position: relative;
	}
</style>
