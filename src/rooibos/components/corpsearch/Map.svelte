<script context="module" lang="ts">
  declare var naver: any;
</script>

<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import SearchBar from './SearchBar.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';

  import {
		showSidebar
	} from '$lib/stores';

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

  let mapInstance: MapInstance | null = null;
  let searchResults: SearchResult[] = [];
  let selectedFilters = {};
  let location: Location | null = null;
  let error: string | null = null;
  let loading = true;
  let script: HTMLScriptElement;
  let searchValue: string = '';

  const userLocation = writable(null);

  const handleSearch = async (searchValue: string, filters: any) => {
    
    if (!mapInstance) return;
    console.log('Searching for:', searchValue, 'with filters:', filters);
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
    handleListIconClick={() => {
      console.log('List icon clicked');
    }}
    isListIconVisible={true}
    isFilterOpen={false}
    setIsFilterOpen={(open) => console.log('Filter open status:', open)}
    toggleFilter={(groupId) => console.log('Toggled filter group:', groupId)}
    activeFilterGroup={null}
    searchResults={searchResults}
  />
</div>

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
  class="absolute bottom-20 right-5 bg-transparent border rounded-full w-12 h-12 flex items-center justify-center shadow-lg z-50"
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

  #map {
    position: relative;
  }
</style>

