<script context="module" lang="ts">
  declare var naver: any;
</script>

<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import SearchBar from './SearchBar.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
  import { compayMarkerInfo } from './companymarkerinfo';
  import { filterGroups } from './filterdata';

  import {
		showSidebar
	} from '$lib/stores';
	import SearchCompanyList from './SearchCompanyList.svelte';
	import SearchFilter from './SearchFilter.svelte';

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

  type SearchResult = {
    company_name: string;
    address: string;
    latitude: string;
    longitude: string;
    phone_number?: string;
    category?: string[];
    // memos?: MemoData[];
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
  const userLocation = writable(null);

  const handleSearch = async (searchValue: string, filters: any) => {
  if (!mapInstance) return;
  console.log('Searching for:', searchValue, 'with filters:', filters);

  try {
    const queryParams = new URLSearchParams({
      query: searchValue,
      latitude: location ? location.lat.toString() : '',
      longitude: location ? location.lng.toString() : '',
      userLatitude: location?.lat?.toString() || '',
      userLongitude: location?.lng?.toString() || '',
      filters: JSON.stringify(filters),
    });

    const response = await fetch(`http://localhost:8080/api/v1/corpsearch?${queryParams.toString()}`, {
      method: 'GET',
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
    } else {
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
    if (mapInstance?.companyMarkers) {
      mapInstance.companyMarkers.forEach(marker => marker.setMap(null));
      mapInstance.companyMarkers = [];
    }
  };

  const handleApply = () => {
    if (!mapInstance) return;
    
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

    naver.maps.Event.addListener(map, 'click', () => {
      infoWindow.close();
      handleSearchListChange(false);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        infoWindow.close();
      }
    });

    mapInstance = { map, marker, infoWindow, companyMarkers: [] };
    loading = false;
  };

  const moveToCurrentLocation = () => {
    if (!location || !mapInstance) {
      alert('현재 위치를 가져올 수 없습니다.');
      return;
    }
    const currentLocation = new naver.maps.LatLng(location.lat, location.lng);
    mapInstance.map.setCenter(currentLocation);
    mapInstance.map.setZoom(15);
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


  // 필터 변경 핸들러
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
    });
  
    selectedFilters = newFilters;
    return newFilters;
  }

  // 필터 초기화 핸들러
  function onReset() {
    selectedFilters = {};
  }

  // 필터 적용 핸들러
  function onApply() {
    activeFilterGroup = null;
  }

  
  const toggleFilter = (groupId: string) => {
    if (mapInstance?.infoWindow) {
      mapInstance.infoWindow.close();
    }
    activeFilterGroup = groupId === activeFilterGroup ? null : groupId;
    isFilterOpen = (groupId !== activeFilterGroup);
    handleSearchListChange(false);
  };

  

</script>
<div 
    class="search-bar-wrapper w-full"
    class:sidebar-visible={$showSidebar}
  >
  <SearchBar
    onSearch={handleSearch}
    onReset={handleReset}
    onApply={handleApply}
    searchValue={searchValue}
    onSearchValueChange={(value) => (searchValue = value)}
    onShowSearchListChange={handleSearchListChange}
    isListIconVisible={isListIconVisible}
    isFilterOpen={isFilterOpen}
    toggleFilter={toggleFilter}
    activeFilterGroup={null}
    searchResults={searchResults}
  />
</div>

{#if searchResults.length > 0 && showSearchList}
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

{#if activeFilterGroup}
  <div 
  class="search-filter-wrapper fixed bottom-0 left-1/2 transform -translate-x-1/2 w-1/2 bg-white border-t border-gray-300 rounded-t-lg shadow-lg p-4 z-[1000]"
  class:sidebar-visible={$showSidebar}>
    <SearchFilter
      {selectedFilters}
      {onFilterChange}
      {onReset}
      {onApply}
      activeGroup={activeFilterGroup}
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

<div id="map" class="w-full h-full relative">
  <div class="absolute top-2 left-2 bg-transparent rounded-full shadow-lg z-50 p-2">
    <div class="{$showSidebar ? 'md:hidden' : ''} self-center flex flex-none items-center">
      <button
        id="sidebar-toggle-button"
        class="cursor-pointer p-1.5 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-850 transition"
        on:click={() => {
          showSidebar.set(!$showSidebar);
        }}
        aria-label="Toggle Sidebar"
      >
        <div class=" m-auto self-center">
          <MenuLines />
        </div>
      </button>
    </div>
  </div>
</div>

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
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 50;
    transition: left 0.3s ease;
  }

  .search-bar-wrapper.sidebar-visible {
    left: calc(50% + 125px);
  }

  .company-list-wrapper {
    position: absolute;
    top: 80px;
    right: 0;
    z-index: 40;
    transition: all 0.3s ease;
    padding: 0 20px;
    left: 0; /* 기본적으로 전체 화면 사용 */
  }

  .company-list-wrapper.sidebar-visible {
    left: 250px !important; /* 사이드바가 보일 때 250px 만큼 띄우기 */
  }

  .search-filter-wrapper.sidebar-visible {
    left: calc(50% + 125px);
  }

  #map {
    position: relative;
  }

  
</style>

