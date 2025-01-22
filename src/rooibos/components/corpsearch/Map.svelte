<script context="module" lang="ts">
  declare var naver: any;
</script>

<script lang="ts">
  import { onMount } from 'svelte';
  import { get, writable } from 'svelte/store';
  import SearchBar from './SearchBar.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
  import { compayMarkerInfo } from './companymarkerinfo';
  import { filterGroups } from './filterdata';
  import { mobile } from '$lib/stores';
  import { showSidebar, user } from '$lib/stores';
	import SearchCompanyList from './SearchCompanyList.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

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
  let isFilterOpen = false;
  let singleClickMarker: any = null;
  let userLocation:UserLocation | null = null;

  const handleSearch = async (searchValue: string, filters: any, ) => {
    if (!mapInstance) return;
    console.log('Searching for:', searchValue, 'with filters:', filters);

    showSearchList = false;
    activeFilterGroup = null;
    isFilterOpen = false;
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
            filters: JSON.stringify(filters),
        });

        const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpsearch/?${queryParams.toString()}`, {
            method: 'GET',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                authorization: `Bearer ${localStorage.token}`,
            },
        });

        if (!response.ok) {
            throw new Error('검색 요청 실패');
        }

        const data = await response.json();
        searchResults = data.data;
        showSearchList = true;

        if (mapInstance?.companyMarkers) {
            mapInstance.companyMarkers.forEach((marker) => marker.setMap(null));
            mapInstance.companyMarkers = [];
        }

        if (mapInstance?.marker) {
            mapInstance.marker.setMap(null);
        }

        if (searchResults.length === 1) {
            const singleResult = searchResults[0];
            const singlePoint = new naver.maps.LatLng(
                parseFloat(singleResult.latitude),
                parseFloat(singleResult.longitude)
            );

            mapInstance?.map.setCenter(singlePoint);
            mapInstance?.map.setZoom(15);

            const marker = new naver.maps.Marker({
                position: singlePoint,
                map: mapInstance.map,
                title: singleResult.company_name,
            });

            naver.maps.Event.addListener(marker, 'click', () => {
                mapInstance?.infoWindow.setContent(compayMarkerInfo(singleResult));
                mapInstance?.infoWindow.open(mapInstance.map, marker);
            });

            mapInstance.companyMarkers.push(marker);

            mapInstance.infoWindow.setContent(compayMarkerInfo(singleResult));
            mapInstance.infoWindow.open(mapInstance.map, marker);
            
        } else if (searchResults.length > 0) {
            // 첫 번째 검색 결과의 위치로 이동
            const firstResult = searchResults[0];
            const firstPoint = new naver.maps.LatLng(
                parseFloat(firstResult.latitude),
                parseFloat(firstResult.longitude)
            );

            mapInstance?.map.setCenter(firstPoint);
            mapInstance.map.setZoom(15);

            searchResults.forEach((result) => {
                const point = new naver.maps.LatLng(
                    parseFloat(result.latitude),
                    parseFloat(result.longitude)
                );

                if (mapInstance) {
                    const marker = new naver.maps.Marker({
                        position: point,
                        map: mapInstance.map,
                        title: result.company_name,
                    });

                    naver.maps.Event.addListener(marker, 'click', () => {
                        mapInstance?.infoWindow.close();
                        mapInstance?.infoWindow.setContent(compayMarkerInfo(result));
                        mapInstance?.infoWindow.open(mapInstance.map, marker);
                    });
                    mapInstance.companyMarkers.push(marker);
                }
            });
            
        }
    } catch (error) {
        console.error('검색 중 오류가 발생했습니다:', error);
    }
  };

  const handleReset = () => {
    selectedFilters = {};    
  };

  const handleApply = () => {
    handleSearch(searchValue, selectedFilters);
    
  };

  const initializeMap = (position: any) => {
    const mapContainer = document.getElementById('map');

    if (!mapContainer) {
      console.error('Map container not found');
      return;
    }


    const mapOptions = {
      center: new naver.maps.LatLng(position.lat, position.lng),
      zoom: 15,
    };

    const map = new naver.maps.Map(mapContainer, mapOptions);
    const marker = new naver.maps.Marker({
      position: new naver.maps.LatLng(position.lat, position.lng),
      map: map,
      
    });

    const infoWindow = new naver.maps.InfoWindow({
      content: '',
      maxWidth: 300,
      backgroundColor: '#fff',
      borderColor: '#5B92E4',
      borderWidth: 2,
      anchorSize: new naver.maps.Size(20, 10),
      pixelOffset: new naver.maps.Point(20, -20),
    });
    
    mapInstance = { map, marker, infoWindow, companyMarkers: [] };
    loading = false;

    naver.maps.Event.addListener(map, 'click', (e: any) => {
      infoWindow.close();
      handleSearchListChange(false);
      handleFilterOpenChange(false);
    });

    naver.maps.Event.addListener(map, 'dragend', (e: any) => {      
      if(location) {
        location.lat = e.coord._lat;
        location.lng = e.coord._lng;
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        infoWindow.close();
      }
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
      mapInstance.map.setZoom(15);
      mapInstance.infoWindow.close();
      
      if (mapInstance.marker) {
        mapInstance.marker.setPosition(currentLocation);
        mapInstance.marker.setMap(mapInstance.map);
      } else {
        mapInstance.marker = new naver.maps.Marker({
          position: currentLocation,
          map: mapInstance.map,
        });
      }
    }    
  };

  const handleResultClick = (result: SearchResult) => {
    if (!mapInstance) return;

    const point = new naver.maps.LatLng(
        parseFloat(result.latitude),
        parseFloat(result.longitude)
    );

    mapInstance.map.setCenter(point);
    mapInstance.map.setZoom(15);
    mapInstance.infoWindow.close();
    mapInstance.infoWindow.setContent(compayMarkerInfo(result));

    const marker = mapInstance.companyMarkers.find(
        (m) => m.getTitle() === result.company_name
    );

    if (marker) {
        mapInstance.infoWindow.open(mapInstance.map, marker);
    }

    showSearchList = false;
    isListIconVisible = !isListIconVisible;
    handleSearchListChange(false);
  };

  const handleSearchListChange = (newValue: boolean) => {
      showSearchList = newValue;
      isListIconVisible = newValue;
      isFilterOpen = false;
  };

  onMount(() => {
    const initialize = async () => {
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject);
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


  function onFilterChange(groupId: string, optionId: string, checked: boolean | string) {
    const group = filterGroups.find((g) => g.id === groupId);
    if (!group) return;
  
    const newFilters = { ...selectedFilters };
  
    if (groupId === 'radius' && typeof checked === 'string') {
      newFilters[groupId] = checked;
    } else if (
      groupId === 'distance' ||
      groupId === 'representative' ||
      groupId === 'gender' || groupId === 'loan'
    ) {
      newFilters[groupId] = checked ? optionId : "";
    }else if (groupId === 'gender_age' && typeof checked === 'string') {
        newFilters[groupId] = checked  
    } else if (typeof checked === 'string') {
      newFilters[groupId] = {
        ...(selectedFilters[groupId] as any),
        [optionId]: checked,
      };
    } else if (group.isMulti) {
      const currentValues = Array.isArray(selectedFilters[groupId])
        ? (selectedFilters[groupId] as string[])
        : [];
      if (checked) {
        newFilters[groupId] = [...currentValues, optionId];
      } else {
        newFilters[groupId] = currentValues.filter((id) => id !== optionId);
      }
    } else {
      newFilters[groupId] = checked ? optionId : "";
    }
  
    Object.keys(newFilters).forEach((key) => {
      if (Array.isArray(newFilters[key]) && newFilters[key].length === 0) {
        delete newFilters[key];
      }
      if (newFilters[key] === null) {
        delete newFilters[key];
      }

      if (typeof newFilters[key] === 'object' && newFilters[key] !== null) {
        const values = Object.values(newFilters[key]);
        if (values.every(val => val === '' || val === null)) {
          delete newFilters[key];
        }
      }
    });
  
    selectedFilters = newFilters;
    return newFilters;
  }

  const handleFilterOpenChange = (value: boolean) => {
    isFilterOpen = value;
  };


</script>
{#if !($showSidebar && $mobile)}
  <div 
      class="search-bar-wrapper w-full"
      class:sidebar-visible={$showSidebar}
    >
    <SearchBar
      onSearch={handleSearch}
      onReset={handleReset}
      onApply={handleApply}
      searchValue={searchValue}
      onShowSearchListChange={handleSearchListChange}
      isListIconVisible={isListIconVisible}
      activeFilterGroup={null}
      onFilterChange={onFilterChange}
      selectedFilters={selectedFilters}
      isFilterOpen={isFilterOpen}
      onFilterOpenChange={handleFilterOpenChange}
    />
  </div>
{/if}

{#if false && searchResults.length > 1 && showSearchList && !($mobile && $showSidebar)}
  <div 
    class="company-list-wrapper w-full"
    class:sidebar-visible={$showSidebar}
    >
      <SearchCompanyList
        searchResults={searchResults}
        onResultClick={handleResultClick}
      />
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

<div id="map" class="w-full h-full relative"/>

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

<style>
.search-bar-wrapper {
  position: absolute;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 50;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.search-bar-wrapper.sidebar-visible {
  left: 210px;
  width: calc(100% - 210px);
  padding-left: 0;
}

/* 768px 이하 모바일 화면에서는 left를 다시 0으로 */
@media (max-width: 768px) {
  .search-bar-wrapper.sidebar-visible {
    left: 250px !important;
  }
}


  .company-list-wrapper {
    position: absolute;
    top: 80px;
    right: 0;
    z-index: 40;
    transition: all 0.3s ease;
    padding: 0 20px;
    left: 0;
  }

  .company-list-wrapper.sidebar-visible {
    left: 250px !important;
  }

  #map {
    position: relative;
  }
  
</style>

