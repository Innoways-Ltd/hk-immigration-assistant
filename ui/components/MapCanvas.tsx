import { MapContainer, TileLayer, Marker, Tooltip, Polyline, useMap } from "react-leaflet";
import { useSettlement } from "@/lib/hooks/use-settlement";
import { useEffect, useMemo } from "react";
import { divIcon, LatLngBounds } from "leaflet";
import { cn } from "@/lib/utils";
import { SettlementCard } from "@/components/SettlementCard";
import { PlaceCard } from "@/components/PlaceCard";
import { useMediaQuery } from "@/lib/hooks/use-media-query";

export type MapCanvasProps = {
  className?: string;
}

// Component to handle user geolocation
function UserLocationMarker() {
  const map = useMap();
  const { settlementPlan } = useSettlement();

  useEffect(() => {
    // Only attempt geolocation if there's no settlement plan yet
    if (settlementPlan) return;

    let isMounted = true;

    // Use browser geolocation API to get user's current position
    if ('geolocation' in navigator) {
      console.log('[UserLocation] Attempting to get user location...');
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          if (!isMounted || !map) return;
          
          const { latitude, longitude } = position.coords;
          console.log('[UserLocation] Got user location:', latitude, longitude);
          
          // Center map on user's location
          map.setView([latitude, longitude], 15, { animate: true });
        },
        (error) => {
          console.warn('[UserLocation] Geolocation error:', error.message);
          // Keep default Hong Kong location on error
        },
        {
          enableHighAccuracy: false,
          timeout: 5000,
          maximumAge: 300000 // 5 minutes cache
        }
      );
    }

    return () => {
      isMounted = false;
    };
  }, [map, settlementPlan]);

  return null;
}

// Component to handle map updates based on focused locations
function MapUpdater() {
  const map = useMap();
  const { focusedLocations, settlementPlan } = useSettlement();

  useEffect(() => {
    // Add safety check for map instance
    if (!map) {
      console.warn('[MapUpdater] Map instance not available');
      return;
    }
    
    // Ensure map container exists
    try {
      const container = map.getContainer();
      if (!container) {
        console.warn('[MapUpdater] Map container not found');
        return;
      }
    } catch (error) {
      console.warn('[MapUpdater] Error accessing map container:', error);
      return;
    }

    // Track if component is still mounted
    let isMounted = true;

    // Use a small delay to ensure map is fully initialized
    const timeoutId = setTimeout(() => {
      if (!isMounted || !map) return;

      try {
        // Check if map container still exists in DOM
        if (!map.getContainer() || !map.getContainer().parentElement) {
          return;
        }

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
            const padding: [number, number] = focusedLocations.length <= 3 ? [80, 80] : [50, 50];
            
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
      } catch (error) {
        // Silently handle errors if map is being unmounted
        console.debug("Map update error (likely during unmount):", error);
      }
    }, 100);

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [map, focusedLocations, settlementPlan]);

  return null;
}

export function MapCanvas({ className }: MapCanvasProps) {
  const { settlementPlan, focusedLocations } = useSettlement();
  const isDesktop = useMediaQuery("(min-width: 900px)");

  // Get IDs of focused locations for highlighting (use useMemo to avoid recreating on every render)
  const focusedLocationIds = useMemo(() => {
    console.log('[MAP DEBUG] Focused locations:', focusedLocations.length, focusedLocations.map(l => `${l.name} (${l.id})`));
    return new Set(focusedLocations.map(loc => loc.id));
  }, [focusedLocations]);

  // Merge service_locations with focused locations to ensure all focused locations are rendered
  const allLocations = useMemo(() => {
    if (!settlementPlan?.service_locations) return [];
    
    const locationMap = new Map();
    
    // First, add all service locations
    settlementPlan.service_locations.forEach(loc => {
      locationMap.set(loc.id, loc);
    });
    
    // Then, add focused locations (will override if ID matches, or add new ones)
    focusedLocations.forEach(loc => {
      if (!locationMap.has(loc.id)) {
        locationMap.set(loc.id, loc);
      }
    });
    
    return Array.from(locationMap.values());
  }, [settlementPlan?.service_locations, focusedLocations]);

  // Use a stable key for MapContainer to prevent remount issues
  const mapKey = settlementPlan?.id || "default-map";

  // Determine map center: use settlement plan if available, otherwise use default Hong Kong location
  // When tasks are generated, the settlement plan will have proper coordinates
  const mapCenter: [number, number] = useMemo(() => {
    if (settlementPlan?.center_latitude && settlementPlan?.center_longitude) {
      return [settlementPlan.center_latitude, settlementPlan.center_longitude];
    }
    // Default to Hong Kong city center (Central)
    return [22.2810, 114.1580];
  }, [settlementPlan]);

  const mapZoom = settlementPlan?.zoom || 13;

  return (
		<div className="relative w-full h-full">
			<MapContainer
				key={mapKey}
				className={cn("w-screen h-screen", className)}
				style={{ zIndex: 0 }}
				center={mapCenter}
				zoom={mapZoom}
				zoomAnimationThreshold={100}
				zoomControl={false}
			>
				<TileLayer
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
				/>
        
        {/* User location tracker - only when no settlement plan */}
        <UserLocationMarker />
        
        {/* Map updater component */}
        <MapUpdater />

        {settlementPlan && allLocations.length > 0 && (
          <>
            {/* Draw path connecting focused locations or all locations */}
            {(focusedLocations.length > 1 ? focusedLocations : allLocations).length > 1 && (
              <Polyline
                positions={(focusedLocations.length > 1 ? focusedLocations : allLocations).map(loc => [loc.latitude, loc.longitude])}
                color={focusedLocations.length > 0 ? "#ef4444" : "#3b82f6"}
                weight={focusedLocations.length > 0 ? 4 : 3}
                opacity={focusedLocations.length > 0 ? 0.8 : 0.6}
                dashArray={focusedLocations.length > 0 ? undefined : "10, 10"}
              />
            )}
            
            {/* Markers for all locations (service + focused) */}
            {allLocations.map((place, i) => {
              const isFocused = focusedLocationIds.has(place.id);
              const isVisible = focusedLocations.length === 0 || isFocused;
              
              if (i === 0) {
                console.log('[MAP DEBUG] Total locations to render:', allLocations.length);
                console.log('[MAP DEBUG] Focused location IDs:', Array.from(focusedLocationIds));
                console.log('[MAP DEBUG] Visible markers:', allLocations.filter((_, idx) => {
                  const focused = focusedLocationIds.has(allLocations[idx].id);
                  return focusedLocations.length === 0 || focused;
                }).length);
              }
              
              // Use stable key based on place.id only (don't include state to avoid remounting)
              const markerKey = `marker-${place.id}-${i}`;
              
              return (
                <Marker 
                  key={markerKey}
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
      {isDesktop && (
        <div className="absolute h-screen top-0 left-0 p-6 pointer-events-none flex items-start w-[35%] md:w-[40%] lg:w-[35%] 2xl:w-[30%]">
          <SettlementCard className="w-full h-full pointer-events-auto" />
        </div>
      )}
		</div>
  );
}
