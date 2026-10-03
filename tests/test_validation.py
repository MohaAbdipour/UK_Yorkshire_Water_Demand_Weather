from final_analysis import windows


def test_expanding_windows_are_disjoint_with_a_year_of_training():
    for n in [100, 364, 454, 512, 1111]:
        blocks = windows(n)
        assert len(blocks) <= 6
        for start, end in blocks:
            assert start >= 365
            assert end - start == 90
            assert end <= n
        assert all(a[1] == b[0] for a,b in zip(blocks,blocks[1:]))
        if blocks:
            assert blocks[-1][1] == n
