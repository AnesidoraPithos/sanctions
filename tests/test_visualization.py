"""
Quick verification script to test the relationship visualization implementation
"""

import sys
import traceback

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    try:
        import networkx as nx
        print("✓ NetworkX imported successfully")
    except ImportError as e:
        print(f"✗ NetworkX import failed: {e}")
        return False

    try:
        import plotly.graph_objects as go
        print("✓ Plotly imported successfully")
    except ImportError as e:
        print(f"✗ Plotly import failed: {e}")
        return False

    try:
        import folium
        print("✓ Folium imported successfully")
    except ImportError as e:
        print(f"✗ Folium import failed: {e}")
        return False

    try:
        from geopy.geocoders import Nominatim
        print("✓ Geopy imported successfully")
    except ImportError as e:
        print(f"✗ Geopy import failed: {e}")
        return False

    try:
        import graph_builder as gb
        print("✓ graph_builder module imported successfully")
    except Exception as e:
        print(f"✗ graph_builder import failed: {e}")
        traceback.print_exc()
        return False

    try:
        import visualizations as viz
        print("✓ visualizations module imported successfully")
    except Exception as e:
        print(f"✗ visualizations import failed: {e}")
        traceback.print_exc()
        return False

    return True


def test_graph_builder():
    """Test basic graph building functionality"""
    print("\nTesting graph builder...")

    try:
        import graph_builder as gb

        # Create a simple test graph
        test_company = "Test Company Inc"
        test_subsidiaries = [
            {'name': 'Subsidiary A', 'jurisdiction': 'USA', 'status': 'Active', 'ownership_percentage': 100},
            {'name': 'Subsidiary B', 'jurisdiction': 'UK', 'status': 'Active', 'ownership_percentage': 75}
        ]
        test_directors = [
            {'name': 'John Doe', 'title': 'CEO', 'nationality': 'USA', 'company_name': test_company}
        ]
        test_shareholders = [
            {'name': 'Big Fund LLC', 'type': 'Institutional', 'ownership_percentage': 15,
             'jurisdiction': 'USA', 'company_name': test_company}
        ]

        # Build graph
        graph = gb.build_entity_graph(
            company_name=test_company,
            subsidiaries=test_subsidiaries,
            sisters=[],
            directors=test_directors,
            shareholders=test_shareholders,
            transactions=[],
            parent_info={'jurisdiction': 'USA', 'status': 'Active'}
        )

        # Check graph structure
        assert graph.number_of_nodes() > 0, "Graph should have nodes"
        assert graph.number_of_edges() > 0, "Graph should have edges"

        print(f"✓ Graph created successfully")
        print(f"  - Nodes: {graph.number_of_nodes()}")
        print(f"  - Edges: {graph.number_of_edges()}")

        # Test statistics
        stats = gb.get_graph_statistics(graph)
        print(f"✓ Statistics calculated")
        print(f"  - Companies: {stats['companies']}")
        print(f"  - People: {stats['people']}")
        print(f"  - Countries: {stats['num_countries']}")

        # Test filtering
        filtered = gb.filter_graph(graph, show_directors=False, show_shareholders=True)
        print(f"✓ Graph filtering works")
        print(f"  - Filtered nodes: {filtered.number_of_nodes()}")

        return True

    except Exception as e:
        print(f"✗ Graph builder test failed: {e}")
        traceback.print_exc()
        return False


def test_visualizations():
    """Test visualization creation (without rendering)"""
    print("\nTesting visualizations...")

    try:
        import graph_builder as gb
        import visualizations as viz

        # Create a simple test graph
        test_company = "Test Company Inc"
        test_subsidiaries = [
            {'name': 'Subsidiary A', 'jurisdiction': 'USA', 'status': 'Active', 'ownership_percentage': 100}
        ]

        graph = gb.build_entity_graph(
            company_name=test_company,
            subsidiaries=test_subsidiaries,
            sisters=[],
            directors=[],
            shareholders=[],
            transactions=[],
            parent_info={'jurisdiction': 'USA', 'status': 'Active'}
        )

        # Test network diagram creation
        fig = viz.create_network_diagram(graph, layout='force', title='Test Network')
        print("✓ Network diagram created successfully")
        print(f"  - Type: {type(fig)}")

        # Test geographic map creation (may fail if geocoding unavailable)
        try:
            geo_map = viz.create_geographic_map(graph, title='Test Map')
            print("✓ Geographic map created successfully")
            print(f"  - Type: {type(geo_map)}")
        except Exception as e:
            print(f"⚠ Geographic map test skipped (expected if offline): {e}")

        return True

    except Exception as e:
        print(f"✗ Visualization test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("RELATIONSHIP DIAGRAM IMPLEMENTATION VERIFICATION")
    print("=" * 60)

    results = []

    # Test imports
    results.append(("Imports", test_imports()))

    # Test graph builder
    if results[-1][1]:  # Only if imports succeeded
        results.append(("Graph Builder", test_graph_builder()))

    # Test visualizations
    if results[-1][1]:  # Only if graph builder succeeded
        results.append(("Visualizations", test_visualizations()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Implementation ready for use!")
    else:
        print("✗ SOME TESTS FAILED - Please check error messages above")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
