import { MapContainer, TileLayer, Marker, Tooltip, Polyline, useMap } from "react-leaflet";
import { useSettlement } from "@/lib/hooks/use-settlement";
import { useEffect, useState } from "react";
import { Map, divIcon, LatLngBounds } from "leaflet";
import { cn } from "@/lib/utils";
import { SettlementCard } from "@/components/SettlementCard";
import { PlaceCard } from "@/components/PlaceCard";
import { useMediaQuery } from "@/lib/hooks/use-media-query";

export type MapCanvasProps = {
  className?: string;
}

// Component to handle map updates based on focused locations
function MapUpdater() {
  const map = useMap();
  const { focusedLocations, settlementPlan } = useSettlement();

  useEffect(() => {
    if (!map) return;

    // If there are focused locations, zoom to them
    if (focusedLocations && focusedLocations.length > 0) {
      if (focusedLocations.length === 1) {
        // Single location: center and zoom in as much as possible
        const loc = focusedLocations[0];
        map.setView([loc.latitude, loc.longitude], 17, { animate: true, duration: 0.5 });
      } else {
        // Multiple locations: fit bounds with maximum zoom
        const bounds = new LatLngBounds(
          focusedLocations.map(loc => [loc.latitude, loc.longitude])
        );
        
        // Calculate optimal padding based on number of locations
        const padding = focusedLocations.length <= 3 ? [80, 80] : [50, 50];
        
        map.fitBounds(bounds, { 
          padding: padding,
          animate: true,
          duration: 0.5,
          maxZoom: 16  // Increased max zoom for better visibility
        });
      }
    } else if (settlementPlan) {
      // No focused locations: show default view
      map.setView(
        [settlementPlan.center_latitude, settlementPlan.center_longitude],
        settlementPlan.zoom || 14,
        { animate: true, duration: 0.5 }
      );
    }
  }, [map, focusedLocations, settlementPlan]);

  return null;
}

export function MapCanvas({ className }: MapCanvasProps) {
  const [map, setMap] = useState<Map | null>(null);
  const { settlementPlan, focusedLocations } = useSettlement();
  const isDesktop = useMediaQuery("(min-width: 900px)");

  // Get IDs of focused locations for highlighting
  const focusedLocationIds = new Set(focusedLocations.map(loc => loc.id));

  return (
		<div className="">
			<MapContainer
				className={cn("w-screen h-screen", className)}
				style={{ zIndex: 0 }}
				center={[0, 0]}
				zoom={1}
				zoomAnimationThreshold={100}
				zoomControl={false}
				ref={setMap}
			>
				<TileLayer
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
				/>
        
        {/* Map updater component */}
        <MapUpdater />

        {settlementPlan && settlementPlan.service_locations && (
          <>
            {/* Draw path connecting focused locations or all locations */}
            {(focusedLocations.length > 1 ? focusedLocations : settlementPlan.service_locations).length > 1 && (
              <Polyline
                positions={(focusedLocations.length > 1 ? focusedLocations : settlementPlan.service_locations).map(loc => [loc.latitude, loc.longitude])}
                color={focusedLocations.length > 0 ? "#ef4444" : "#3b82f6"}
                weight={focusedLocations.length > 0 ? 4 : 3}
                opacity={focusedLocations.length > 0 ? 0.8 : 0.6}
                dashArray={focusedLocations.length > 0 ? undefined : "10, 10"}
              />
            )}
            
            {/* Markers for service locations */}
            {settlementPlan.service_locations.map((place, i) => {
              const isFocused = focusedLocationIds.has(place.id);
              const isVisible = focusedLocations.length === 0 || isFocused;
              
              return (
                <Marker 
                  key={i} 
                  position={[place.latitude, place.longitude]}
                  icon={divIcon({
                    className: "bg-transparent",
                    html: `<div class="${isFocused ? 'bg-red-500 scale-125' : 'bg-blue-500'} text-white w-8 h-8 rounded-full flex items-center justify-center font-bold border-2 border-white shadow-lg transition-all duration-300" style="display: ${isVisible ? 'flex' : 'none'}">${i + 1}</div>`,
                    iconSize: [32, 32],
                    iconAnchor: [16, 16],
                  })}
                  opacity={isVisible ? 1 : 0.3}
                >
                  <Tooltip offset={[10, 0]} opacity={1}>
                    <PlaceCard shouldShowCheckbox={false} className="border-none overflow-y-auto shadow-none" place={place} />
                  </Tooltip>
                </Marker>
              );
            })}
          </>
        )}
      </MapContainer>
      {map && isDesktop && (
        <div className="absolute h-screen top-0 left-0 p-6 pointer-events-none flex items-start w-[35%] md:w-[40%] lg:w-[35%] 2xl:w-[30%]">
          <SettlementCard className="w-full h-full pointer-events-auto" />
        </div>
      )}
		</div>
  );
}
