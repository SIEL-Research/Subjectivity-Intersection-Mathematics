#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Luke Kenneth Casson Leighton
#
# Dual-ring Boolean playground for the proposed CDC-6600-inspired
# READ / EXECUTE / WRITE control kernel.
#
# Deliberate restrictions:
#   - Python 3 standard library only
#   - no classes
#   - no dataclasses
#   - no type hints
#   - state held in dicts, tuples and bools
#
# Architecture:
#
#   Clockwise ring:
#       A+ -> B+ -> C+ -> A+
#
#   Anticlockwise ring:
#       A- -> C- -> B- -> A-
#
#   Six full adders total:
#       A+, B+, C+, A-, B-, C-
#
#   Each full adder receives:
#       x_i = NOT Q_i
#       H   = common all-ones / inverter control
#       Z   = common reset control
#
#   Each full adder produces:
#       S_i = x_i XOR H XOR Z
#       C_i = majority(x_i, H, Z)
#
#   Local control table:
#
#       H Z | SUM   CARRY
#       ----+------------
#       0 0 | x       0
#       0 1 | NOT x   x
#       1 0 | NOT x   x
#       1 1 | x       1
#
#   Therefore the CARRY column is:
#
#       0, x, x, 1
#
# Operational mode:
#
#       H XOR Z = 1
#
# gives:
#
#       SUM_i   = Q_i
#       CARRY_i = NOT Q_i
#       SUM_i XOR CARRY_i = 1
#
# independently for all six adders.
#
# The twelve raw adder outputs pass through twelve matched one-clock
# observation buffers before comparison:
#
#       D+ = buffered_SUM+ XOR buffered_CARRY+ = 111
#       D- = buffered_SUM- XOR buffered_CARRY- = 111
#
# The final orientation-independent readouts are:
#
#       CIT_WORD  = D+ AND D-        = 111
#       AGREEMENT = D+ XNOR D-       = 111
#       CIT       = AND-reduce(CIT_WORD) = 1
#
# The state latches update once per clock from the unbuffered adder outputs.
# SUM drives SET and CARRY drives RESET after orientation-specific rotation.
# RESET is dominant.
#
# Double-high mode:
#
#       H = 1, Z = 1
#
# gives CARRY_i = 1 for every local state, therefore both triplets are
# forced to the rare all-zero fixed state on the next clock.
#
# This is a compact falsifiable playground, not a transistor-accurate
# reconstruction of the historical CDC 6600.
#
# Examples:
#
#   ./cdc6600_dual_ring_cit_demo.py --demo
#   ./cdc6600_dual_ring_cit_demo.py --self-test
#   ./cdc6600_dual_ring_cit_demo.py --steps 9
#   ./cdc6600_dual_ring_cit_demo.py --invert 1 --reset 1 --steps 3
#

import argparse
import itertools
import sys


LABELS = ("A", "B", "C")
ZERO = (False, False, False)


def full_adder(a, b, c):
    """Return one-bit SUM and CARRY."""
    a = bool(a)
    b = bool(b)
    c = bool(c)

    sum_bit = a ^ b ^ c
    carry_bit = (a and b) or (b and c) or (c and a)

    return sum_bit, carry_bit


def rotate(bits, direction):
    """
    Rotate a three-bit word.

    Word order is (A, B, C).

    cw:
        A -> B -> C -> A
        (A, B, C) becomes (C, A, B)

    ccw:
        A -> C -> B -> A
        (A, B, C) becomes (B, C, A)
    """
    bits = tuple(bits)

    if direction == "cw":
        return bits[2], bits[0], bits[1]

    if direction == "ccw":
        return bits[1], bits[2], bits[0]

    raise ValueError("direction must be 'cw' or 'ccw'")


def local_adders(state, inverter, reset):
    """Evaluate one oriented triplet of three local full adders."""
    sums = []
    carries = []

    for q_bit in state:
        x_bit = not q_bit
        sum_bit, carry_bit = full_adder(
            x_bit,
            inverter,
            reset,
        )
        sums.append(sum_bit)
        carries.append(carry_bit)

    return tuple(sums), tuple(carries)


def delayed_sr_latch(old_q, set_bit, reset_bit):
    """
    One-clock reset-dominant SR latch.

    The combinational inputs are sampled at this clock edge and the
    returned Q value is the next-clock state.
    """
    if reset_bit:
        return False

    if set_bit:
        return True

    return bool(old_q)


def ring_next(state, sums, carries, direction):
    """
    Route one triplet around its orientation and update all three latches.
    """
    set_inputs = rotate(sums, direction)
    reset_inputs = rotate(carries, direction)

    next_state = []

    for index in range(3):
        next_state.append(
            delayed_sr_latch(
                state[index],
                set_inputs[index],
                reset_inputs[index],
            )
        )

    return (
        tuple(next_state),
        set_inputs,
        reset_inputs,
    )


def xor_words(left, right):
    return tuple(a ^ b for a, b in zip(left, right))


def xnor_words(left, right):
    return tuple(not (a ^ b) for a, b in zip(left, right))


def and_words(left, right):
    return tuple(a and b for a, b in zip(left, right))


def and_reduce(bits):
    result = True

    for bit in bits:
        result = result and bit

    return result


def one_clock_buffer(inputs):
    """
    A conceptual matched one-clock buffer.

    The caller stores the returned tuple as next-buffer state.  Comparison
    in the current row uses the previous buffer state.
    """
    return tuple(bool(bit) for bit in inputs)


def make_machine(cw_state, ccw_state):
    return {
        "cw_state": tuple(cw_state),
        "ccw_state": tuple(ccw_state),
        "cw_sum_buf": ZERO,
        "cw_carry_buf": ZERO,
        "ccw_sum_buf": ZERO,
        "ccw_carry_buf": ZERO,
    }


def buffered_readout(machine):
    """
    Compare only matched, same-epoch buffered outputs.
    """
    cw_diff = xor_words(
        machine["cw_sum_buf"],
        machine["cw_carry_buf"],
    )
    ccw_diff = xor_words(
        machine["ccw_sum_buf"],
        machine["ccw_carry_buf"],
    )

    cit_word = and_words(cw_diff, ccw_diff)
    agreement = xnor_words(cw_diff, ccw_diff)
    cit = and_reduce(cit_word)

    return {
        "cw_diff": cw_diff,
        "ccw_diff": ccw_diff,
        "cit_word": cit_word,
        "agreement": agreement,
        "cit": cit,
    }


def tick(machine, inverter, reset):
    """
    Advance both oriented triplets by one clock.

    The old matched buffers are compared in this row.
    Current raw adder outputs are loaded into the buffers for the next row.
    """
    readout = buffered_readout(machine)

    cw_sums, cw_carries = local_adders(
        machine["cw_state"],
        inverter,
        reset,
    )
    ccw_sums, ccw_carries = local_adders(
        machine["ccw_state"],
        inverter,
        reset,
    )

    cw_next, cw_set, cw_reset = ring_next(
        machine["cw_state"],
        cw_sums,
        cw_carries,
        "cw",
    )
    ccw_next, ccw_set, ccw_reset = ring_next(
        machine["ccw_state"],
        ccw_sums,
        ccw_carries,
        "ccw",
    )

    next_machine = {
        "cw_state": cw_next,
        "ccw_state": ccw_next,
        "cw_sum_buf": one_clock_buffer(cw_sums),
        "cw_carry_buf": one_clock_buffer(cw_carries),
        "ccw_sum_buf": one_clock_buffer(ccw_sums),
        "ccw_carry_buf": one_clock_buffer(ccw_carries),
    }

    row = {
        "cw_state": machine["cw_state"],
        "ccw_state": machine["ccw_state"],
        "cw_raw_sum": cw_sums,
        "cw_raw_carry": cw_carries,
        "ccw_raw_sum": ccw_sums,
        "ccw_raw_carry": ccw_carries,
        "cw_set": cw_set,
        "cw_reset": cw_reset,
        "ccw_set": ccw_set,
        "ccw_reset": ccw_reset,
        "cw_diff": readout["cw_diff"],
        "ccw_diff": readout["ccw_diff"],
        "cit_word": readout["cit_word"],
        "agreement": readout["agreement"],
        "cit": readout["cit"],
        "cw_next": cw_next,
        "ccw_next": ccw_next,
    }

    return next_machine, row


def parse_bits(text):
    if len(text) != 3:
        raise ValueError("state must contain exactly three bits")

    if any(char not in "01" for char in text):
        raise ValueError("state must contain only 0 and 1")

    return tuple(char == "1" for char in text)


def bits_text(bits):
    return "".join("1" if bit else "0" for bit in bits)


def bool_text(value):
    return "1" if value else "0"


def print_mode_table():
    print("Local full-adder Boolean table")
    print()
    print("H Z | SUM   CARRY")
    print("----+------------")
    print("0 0 | x       0")
    print("0 1 | NOT x   x")
    print("1 0 | NOT x   x")
    print("1 1 | x       1")
    print()
    print("CARRY sequence: 0, x, x, 1")
    print()


def print_header():
    print(
        "tick  CW_Q CCW_Q | CW_S CW_C | CCW_S CCW_C | "
        "D+  D-  CITW AGR CIT | CW_Q' CCW_Q'"
    )
    print(
        "----  ---- ----- | ---- ---- | ------ ------ | "
        "--- --- ---- --- --- | ----- ------"
    )


def print_row(index, row):
    print(
        "%4d  %s  %s | %s  %s | %s   %s | "
        "%s %s %s  %s  %s  | %s   %s"
        % (
            index,
            bits_text(row["cw_state"]),
            bits_text(row["ccw_state"]),
            bits_text(row["cw_raw_sum"]),
            bits_text(row["cw_raw_carry"]),
            bits_text(row["ccw_raw_sum"]),
            bits_text(row["ccw_raw_carry"]),
            bits_text(row["cw_diff"]),
            bits_text(row["ccw_diff"]),
            bits_text(row["cit_word"]),
            bits_text(row["agreement"]),
            bool_text(row["cit"]),
            bits_text(row["cw_next"]),
            bits_text(row["ccw_next"]),
        )
    )


def run_trace(
    cw_state,
    ccw_state,
    inverter,
    reset,
    steps,
):
    machine = make_machine(cw_state, ccw_state)

    print(
        "H=%s Z=%s; first row is matched-buffer warm-up"
        % (
            bool_text(inverter),
            bool_text(reset),
        )
    )
    print_header()

    for index in range(steps):
        machine, row = tick(
            machine,
            inverter,
            reset,
        )
        print_row(index, row)

    print()


def all_states():
    states = []

    for number in range(8):
        states.append(
            (
                bool(number & 4),
                bool(number & 2),
                bool(number & 1),
            )
        )

    return states


def check_operational_raw_invariant():
    """
    For every pair of CW and CCW states and either single-high control mode,
    both raw local XOR words must equal 111.
    """
    ones = (True, True, True)

    for cw_state in all_states():
        for ccw_state in all_states():
            for inverter, reset in (
                (True, False),
                (False, True),
            ):
                cw_sum, cw_carry = local_adders(
                    cw_state,
                    inverter,
                    reset,
                )
                ccw_sum, ccw_carry = local_adders(
                    ccw_state,
                    inverter,
                    reset,
                )

                if xor_words(cw_sum, cw_carry) != ones:
                    return False

                if xor_words(ccw_sum, ccw_carry) != ones:
                    return False

    return True


def check_matched_buffer_invariant():
    """
    After one warm-up clock, matched buffered comparisons must both be 111
    for every pair of initial states in operational mode.
    """
    ones = (True, True, True)

    for cw_state in all_states():
        for ccw_state in all_states():
            machine = make_machine(cw_state, ccw_state)

            machine, unused_row = tick(
                machine,
                True,
                False,
            )
            machine, row = tick(
                machine,
                True,
                False,
            )

            if row["cw_diff"] != ones:
                return False

            if row["ccw_diff"] != ones:
                return False

            if row["cit_word"] != ones:
                return False

            if row["agreement"] != ones:
                return False

            if not row["cit"]:
                return False

    return True


def check_double_high_reset():
    """
    Double-high must force both oriented latch triplets to 000 in one clock.
    """
    for cw_state in all_states():
        for ccw_state in all_states():
            machine = make_machine(cw_state, ccw_state)
            machine, unused_row = tick(
                machine,
                True,
                True,
            )

            if machine["cw_state"] != ZERO:
                return False

            if machine["ccw_state"] != ZERO:
                return False

    return True


def check_oriented_cycles():
    """
    Starting from 100 in operational mode:

      CW:  100 -> 010 -> 001 -> 100
      CCW: 100 -> 001 -> 010 -> 100
    """
    machine = make_machine(
        (True, False, False),
        (True, False, False),
    )

    expected_cw = [
        "100",
        "010",
        "001",
        "100",
    ]
    expected_ccw = [
        "100",
        "001",
        "010",
        "100",
    ]

    seen_cw = [bits_text(machine["cw_state"])]
    seen_ccw = [bits_text(machine["ccw_state"])]

    for unused_index in range(3):
        machine, unused_row = tick(
            machine,
            True,
            False,
        )
        seen_cw.append(bits_text(machine["cw_state"]))
        seen_ccw.append(bits_text(machine["ccw_state"]))

    return seen_cw == expected_cw and seen_ccw == expected_ccw


def self_test():
    tests = [
        (
            "operational raw D+=D-=111",
            check_operational_raw_invariant,
        ),
        (
            "matched one-clock buffers preserve 111",
            check_matched_buffer_invariant,
        ),
        (
            "double-high forces both rings to 000",
            check_double_high_reset,
        ),
        (
            "CW and CCW one-hot cycles are opposite",
            check_oriented_cycles,
        ),
    ]

    failed = 0

    for name, function in tests:
        passed = function()
        print(("%-48s %s") % (name, "PASS" if passed else "FAIL"))

        if not passed:
            failed += 1

    if failed:
        print()
        print("%d self-test(s) failed" % failed)
        return 1

    print()
    print("all self-tests passed")
    return 0


def demo():
    print_mode_table()

    print("Operational dual-ring cycle")
    print("---------------------------")
    run_trace(
        (True, False, False),
        (True, False, False),
        True,
        False,
        7,
    )

    print("Double-high invariant/reset")
    print("---------------------------")
    run_trace(
        (True, True, True),
        (False, True, True),
        True,
        True,
        3,
    )

    print("Self-test")
    print("---------")
    self_test()


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Dual clockwise/anticlockwise Boolean full-adder "
            "Cit-invariance playground"
        )
    )

    parser.add_argument(
        "--cw-state",
        default="100",
        help="initial clockwise A/B/C state, default: 100",
    )
    parser.add_argument(
        "--ccw-state",
        default="100",
        help="initial anticlockwise A/B/C state, default: 100",
    )
    parser.add_argument(
        "--invert",
        type=int,
        choices=(0, 1),
        default=1,
        help="common all-ones/inverter input H",
    )
    parser.add_argument(
        "--reset",
        type=int,
        choices=(0, 1),
        default=0,
        help="common reset input Z",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=8,
        help="number of clocks to run",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="print the local 0,x,x,1 Boolean table",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run exhaustive invariant checks",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run operational and reset demonstrations",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.steps < 1:
        parser.error("--steps must be at least 1")

    try:
        cw_state = parse_bits(args.cw_state)
        ccw_state = parse_bits(args.ccw_state)
    except ValueError as error:
        parser.error(str(error))

    if args.demo:
        demo()
        return 0

    if args.table:
        print_mode_table()

    if args.self_test:
        return self_test()

    run_trace(
        cw_state,
        ccw_state,
        bool(args.invert),
        bool(args.reset),
        args.steps,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
