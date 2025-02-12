export class OverlappingMarkerSpiderfier {
  private markers: any[] = [];
  private spiderfiedMarkers: any[] = [];
  private map: any;
  private currentSpiderifiedCluster: any = null;
  private readonly SPIRAL_POSITIONS = 8;
  private readonly RADIUS = 80; // 반경을 더 크게 설정

  constructor(map: any) {
      this.map = map;
  }

  addMarker(marker: any) {
      this.markers.push(marker);
      this.bindMarkerEvents(marker);
  }

  private findOverlappingMarkers(targetMarker: any): any[] {
      const overlapping: any[] = [];
      const targetPos = targetMarker.getPosition();
      const OVERLAP_DISTANCE = 40; // 겹침 판단 거리
      
      // 첫 번째 패스: 직접적으로 겹치는 마커들 찾기
      const directOverlaps = this.markers.filter(marker => {
          if (marker === targetMarker) return false;
          
          const pos = marker.getPosition();
          const distance = this.getPixelDistance(targetPos, pos);
          return distance < OVERLAP_DISTANCE;
      });

      if (directOverlaps.length === 0) return [];

      // 두 번째 패스: 겹치는 마커들 간의 연결 관계 확인
      const visited = new Set([targetMarker]);
      const queue = [...directOverlaps];
      
      while (queue.length > 0) {
          const currentMarker = queue.shift()!;
          if (visited.has(currentMarker)) continue;
          
          visited.add(currentMarker);
          overlapping.push(currentMarker);
          
          const currentPos = currentMarker.getPosition();
          const neighbors = this.markers.filter(marker => {
              if (visited.has(marker)) return false;
              
              const pos = marker.getPosition();
              const distance = this.getPixelDistance(currentPos, pos);
              return distance < OVERLAP_DISTANCE;
          });
          
          queue.push(...neighbors);
      }

      // 거리에 따라 정렬하여 일관된 순서 보장
      overlapping.sort((a, b) => {
          const distA = this.getPixelDistance(targetPos, a.getPosition());
          const distB = this.getPixelDistance(targetPos, b.getPosition());
          return distA - distB;
      });

      return overlapping;
  }

  private getPixelDistance(pos1: any, pos2: any): number {
      const proj = this.map.getProjection();
      const pos1Px = proj.fromCoordToOffset(pos1);
      const pos2Px = proj.fromCoordToOffset(pos2);
      
      // 정확한 픽셀 거리 계산을 위해 소수점 처리
      const dx = Math.round((pos1Px.x - pos2Px.x) * 100) / 100;
      const dy = Math.round((pos1Px.y - pos2Px.y) * 100) / 100;
      
      return Math.sqrt(dx * dx + dy * dy);
  }

  private spiderfy(marker: any, overlappingMarkers: any[]) {
      if (this.currentSpiderifiedCluster === marker) {
          return; // 같은 마커를 다시 클릭한 경우 무시
      }
      
      if (this.currentSpiderifiedCluster) {
          this.unspiderfy();
      }

      const position = marker.getPosition();
      const allMarkers = [marker, ...overlappingMarkers];
      const proj = this.map.getProjection();
      const centerPos = proj.fromCoordToOffset(position);
      const angleStep = (2 * Math.PI) / allMarkers.length;
      const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5', '#9A7AA0', '#87A9D6'];

      allMarkers.forEach((m: any, index: number) => {
          const angle = index * angleStep;
          const pixelX = centerPos.x + this.RADIUS * Math.cos(angle);
          const pixelY = centerPos.y + this.RADIUS * Math.sin(angle);
          
          const newPos = proj.fromOffsetToCoord(new naver.maps.Point(pixelX, pixelY));
          const markerColor = colors[index % colors.length];
          
          // 라인 스타일 개선
          const legLine = new naver.maps.Polyline({
              path: [position, newPos],
              strokeWeight: 2,
              strokeColor: markerColor,
              strokeOpacity: 0.8,
              map: this.map
          });

          // 마커 스타일 변경
          const originalContent = m.getIcon().content;
          const coloredContent = originalContent.replace(
              'background: white;',
              `background: ${markerColor}; color: white;`
          ).replace(
              'border: 1px solid #888;',
              `border: 2px solid ${markerColor};`
          ).replace(
              'border-top: 8px solid white;',
              `border-top: 8px solid ${markerColor};`
          ).replace(
              'border-top: 8px solid #888;',
              `border-top: 8px solid ${markerColor};`
          );

          m.setIcon({
              ...m.getIcon(),
              content: coloredContent
          });

          m.setPosition(newPos);
          m.setZIndex(200);
          
          this.spiderfiedMarkers.push({
              marker: m,
              originalPosition: position,
              line: legLine,
              originalIcon: originalContent
          });
      });

      this.currentSpiderifiedCluster = marker;
  }

  private unspiderfy() {
      if (!this.spiderfiedMarkers.length) return;

      this.spiderfiedMarkers.forEach(({ marker, originalPosition, line, originalIcon }) => {
          marker.setPosition(originalPosition);
          marker.setZIndex(100);
          marker.setIcon({
              ...marker.getIcon(),
              content: originalIcon
          });
          line.setMap(null);
      });

      this.spiderfiedMarkers = [];
      this.currentSpiderifiedCluster = null;
  }

  private bindMarkerEvents(marker: any) {
      naver.maps.Event.addListener(marker, 'click', () => {
          const overlapping = this.findOverlappingMarkers(marker);
          
          if (overlapping.length > 0) {
              this.spiderfy(marker, overlapping);
          }
      });

      naver.maps.Event.addListener(this.map, 'zoom_changed', () => {
          this.unspiderfy();
      });
  }
}