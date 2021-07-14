# New Transaction Set Guide

This guide documents the process used to add a new transaction set to LinuxForHealth x12. Please review this guide and
the implementation within the `x12_270_005010X279A1` transaction set before adding a new transaction.

## Add Transaction Package

Add a new transaction package to `x12.transactions` for the transaction set. The new transaction package name must
adhere to the following convention to support transaction discovery - `x12_[transaction set code]_[implementation version]`.

Add the following modules to the new transaction package:

* __init__.py (required to support the new package)
* loops.py
* parsing.py
* segments.py
* transaction_set.py

## Add Segments

Review the transaction specification and determine if all segments within the transaction set are supported within the
`x12.segments` module. 

If a segment is missing from the `x12.segments` module, add a new entry to `x12.models.X12SegmentName`

```python
from enum import Enum

class X12SegmentName(str, Enum):
    """
    Supported X12 Segment Names
    """

    BHT = "BHT"
    GE = "GE"
    GS = "GS"
    HL = "HL"
    # etc
```

Next, create a new model by extending the `X12Segment` class. 

Each new model must override the `segment_name` attribute to support the appropriate `X12SegmentName` enumeration value.
Models use Pydantic field type constraints to ensure that field types adhere to the X12 specification.

The example below illustrates the following:

* The `GeSegment` class overrides `segment_name` to support the appropriate enumeration value.
* The Pydantic constrained type `PositiveInt` ensures that `number_of_transaction_sets_included` is a positive integer.
* A Pydantic `Field` type ensures that `group_control_number` has a constrained width.


```python
from x12.models import X12Segment, X12SegmentName
from pydantic import PositiveInt, Field

class GeSegment(X12Segment):
    """
    Defines a functional header for the message and is an EDI control segment.
    Example:
        GE*1*1~
    """

    segment_name: X12SegmentName = X12SegmentName.GE
    number_of_transaction_sets_included: PositiveInt
    group_control_number: str = Field(min_length=1, max_length=9)


```

Next, add specialized segment models to `x12.transactoins.[new transaction package].segments.py`as necessary.
Each specialized model must extend its base segment model counterpart.

In the example below `Loop2000AHlSegment` extends `HlSegment` with overrides appropriate for the Eligibility (270)
Transaction's 2000A Loop (Information Receiver).  

The `Loop2000AHlSegment` provides the following:

* A clear type name that includes the loop context, Loop 2000A, and the segment, HL.
* A nested enum class used to specify valid field values. The enum is nested since it's usage is limited to this loop/segment/field.
* The class overrides `hierarchical_id_number` to specify that it may only accept a single, literal value.
* The class overrides `hierarchical_parent_id_number` to set it as `Optional` since it is not required in the 2000A loop.

```python
from x12.segments import HlSegment
from enum import Enum
from typing import Literal, Optional

class Loop2000AHlSegment(HlSegment):
    """
    Loop2000A HL segment adjusted for Information Source usage
    Example:
        HL*1**20*1~
    """

    class HierarchicalLevelCode(str, Enum):
        """
        Code value for HL03
        """

        INFORMATION_SOURCE = "20"

    hierarchical_id_number: Literal["1"]
    hierarchical_parent_id_number: Optional[str]
    hierarchical_level_code: HierarchicalLevelCode
```
## Add Header and Footer Loop Models

Create loop models which extend the `x12.models.X12SegmentGroup` to support the transaction set's header and footer.
Typically, the header supports the `ST` segment while the footer supports the `SE` segment. Review the specification to
determine if additional segments should be included in the header or footer. 

The following example is from the Eligibility (270) loop modules.

The Header loop model includes two segments, `ST` and `BHT`.  The `ST` segment, `HeaderStSegment` is a specialized segment
which overrides transaction set fields as appropriate to specify the Eligibility (270) transaction.

The Footer loop model uses the "standard" or "base" `SE` segment from the `x12.segments` module.

```python
from x12.models import X12SegmentGroup
from x12.segments import SeSegment
from x12.transactions.x12_270_005010X279A1.segments import (
    HeaderBhtSegment,
    HeaderStSegment,
)

class Header(X12SegmentGroup):
    """
    Transaction Header Information
    """

    st_segment: HeaderStSegment
    bht_segment: HeaderBhtSegment

class Footer(X12SegmentGroup):
    """
    Transaction Footer Information
    """

    se_segment: SeSegment
```
## Add Additional Loop Models

Create additional models to support the transaction set's loop groupings. Use the same approach taken when creating the
Header and Footer models.

## Add Transaction Set Model

The transaction set model is defined within the `transaction_set.py` module. The transaction set model must extend 
`x12.models.X12SegmentGroup`.

```python
from typing import List
from x12.models import X12SegmentGroup
from x12.transactions.x12_270_005010X279A1.loops import Footer, Header, Loop2000A


class EligibilityInquiry(X12SegmentGroup):
    """ """
    header: Header
    # the transaction set is nested within the 2000A loop
    loop_2000a: List[Loop2000A]
    footer: Footer
```

## Add Transaction Set Parser and Loop Parsing Functions

LinuxForHealth x12 decouples segment parsing from segment iteration/io. To implement a parser, create a new class within
the parsing module that extends `x12.parsing.X12Parser`. The new parser must set the `self._model_class` attribute
to the appropriate transaction set model. The requirement to create a parser subclass is superfluous, and will be
removed in a future PR.


```python
from x12.parsing import X12Parser
from x12.models import X12Delimiters
from x12.transactions.x12_270_005010X279A1 import EligibilityInquiry

class EligibilityInquiryParser(X12Parser):
    """
    The 270 005010X279A1 parser.
    """

    def __init__(self, x12_delimiters: X12Delimiters):
        """
        Configures the Eligibility 270 Transactions parser.

        :param x12_delimiters: The delimiters used in the 270 message
        """
        super().__init__(x12_delimiters)
        self._model_class = EligibilityInquiry
    

```

Each parsing module includes parsing functions which are used to create loop containers within the transaction set
data record. Loop parsing functions use the `match` decorator to identify the loop's first segment and provide additional
matching conditions, if needed.

```python
from x12.parsing import match, X12ParserContext
from x12.transactions.x12_270_005010X279A1.parsing import TransactionLoops

@match("HL", conditions={"hierarchical_level_code": "20"})
def set_information_source_hl_loop(context: X12ParserContext):
    """
    Sets the Information Source (Payer/Clearinghouse) loop.

    :param context: The X12Parsing context which contains the current loop and transaction record.
    """

    if TransactionLoops.INFORMATION_SOURCE not in context.transaction_data:
        context.transaction_data[TransactionLoops.INFORMATION_SOURCE] = [{}]
    else:
        context.transaction_data[TransactionLoops.INFORMATION_SOURCE].append({})

    info_source = context.transaction_data[TransactionLoops.INFORMATION_SOURCE][-1]
    context.set_loop_context(TransactionLoops.INFORMATION_SOURCE, info_source)

```

## Testing

Transaction testing verifies x12 generation at the transaction level with use-case specific messages. Loop level and
segment level testing is omitted due to the overlap with transactional testing.