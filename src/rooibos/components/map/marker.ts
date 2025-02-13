export function getMarkerContent(result: any, selected: boolean = false): string {
    const background = selected ? "#ffeb3b" : "white";
    const border = selected ? "2px solid #fbc02d" : "1px solid #888";
    return `
            <div class="marker-content" style="
                position: relative;
                padding: 8px;
                background: ${background};
                border: ${border};
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
                    border-top: 8px solid ${selected ? "#fbc02d" : "white"};
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
                    border-top: 8px solid ${selected ? "#fbc02d" : "#888"};
                    z-index: -1;
                "></div>
                <div style="font-weight: bold; color: #666;">${result.company_name}(${result.business_registration_number})</div>
                <div style="font-size: 11px; color: #666; margin-top: 2px;">
                    ${result.representative || '대표자 미상'}
                </div>
            </div>
            `;
}

export const darkStyle = [
    {
        "featureType": "all",
        "elementType": "geometry",
        "stylers": [
            { "color": "#2c2c2c" }
        ]
    },
    {
        "featureType": "all",
        "elementType": "labels.text.fill",
        "stylers": [
            { "color": "#ffffff" }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "geometry.fill",
        "stylers": [
            { "color": "#222222" }
        ]
    },
    {
        "featureType": "poi",
        "elementType": "geometry.fill",
        "stylers": [
            { "color": "#333333" }
        ]
    },
    {
        "featureType": "road",
        "elementType": "geometry",
        "stylers": [
            { "color": "#444444" }
        ]
    },
    {
        "featureType": "water",
        "elementType": "geometry.fill",
        "stylers": [
            { "color": "#000000" }
        ]
    }
];