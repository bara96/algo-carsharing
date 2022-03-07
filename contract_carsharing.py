from pyteal import *


# Handle each possible OnCompletion type. We don't have to worry about
# handling ClearState, because the ClearStateProgram will execute in that
# case, not the ApprovalProgram.
def approval_program():
    handle_creation = Seq([
        App.globalPut(Bytes("Creator"), Txn.sender()),
        Assert(Txn.application_args.length() == Int(7)),
        App.globalPut(Bytes("Name"), Btoi(Txn.application_args[0])),
        App.globalPut(Bytes("Departure_Address"), Txn.application_args[1]),
        App.globalPut(Bytes("Arrival_Address"), Txn.application_args[2]),
        App.globalPut(Bytes("Departure_Date"), Txn.application_args[3]),
        App.globalPut(Bytes("Arrival_Date"), Txn.application_args[4]),
        App.globalPut(Bytes("Trip_Cost"), Btoi(Txn.application_args[5])),
        App.globalPut(Bytes("Max_Participants"), Btoi(Txn.application_args[6])),
        Return(Int(1))
    ])

    handle_optin = Seq([
        Return(Int(1))
    ])

    handle_closeout = Seq([
        Return(Int(1))
    ])

    is_creator = Txn.sender() == App.globalGet(Bytes("Creator"))

    # Declare the ScratchVar as a Python variable _outside_ the expression tree
    scratchCount = ScratchVar(TealType.uint64)

    add = Seq(
        # The initial `store` for the scratch var sets the value to
        # whatever is in the `Count` global state variable
        scratchCount.store(App.globalGet(Bytes("Count"))),
        # Increment the value stored in the scratch var
        # and update the global state variable
        App.globalPut(Bytes("Count"), scratchCount.load() + Int(1)),
        App.localPut(Int(0), Bytes("Count"), scratchCount.load() + Int(1)),
        Return(Int(1))
    )

    deduct = Seq(
        # The initial `store` for the scratch var sets the value to
        # whatever is in the `Count` global state variable
        scratchCount.store(App.globalGet(Bytes("Count"))),
        # Check if the value would be negative by decrementing
        If(scratchCount.load() > Int(0),
           # If the value is > 0, decrement the value stored
           # in the scratch var and update the global state variable
           App.globalPut(Bytes("Count"), scratchCount.load() - Int(1)),
           App.localPut(Int(0), Bytes("Count"), scratchCount.load() - Int(1)),
           ),
        Return(Int(1))
    )

    handle_noop = Seq(
        Assert(Global.group_size() == Int(1)),
        Cond(
            [Txn.application_args[0] == Bytes("Add"), add],
            [Txn.application_args[0] == Bytes("Deduct"), deduct]
        )
    )

    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return program

def clear_state_program():
    program = Seq([
        Return(Int(1))
    ])

    return program


with open('carsharing_approval.teal', 'w') as f:
    compiled = compileTeal(approval_program(), Mode.Application, version=5)
    f.write(compiled)

with open('carsharing_clear_state.teal', 'w') as f:
    compiled = compileTeal(clear_state_program(), Mode.Application, version=5)
    f.write(compiled)